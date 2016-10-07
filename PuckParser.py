from PuckScanner import *
import PuckImpl

class PuckParser( object ):
   def __init__( self, globalEnvironment ):
      self._scanner    = PuckScanner( )
      self._currentEnv = globalEnvironment

   def parse( self, inputString ):
      self._scanner.reset( inputString )

      pkExprObj = self._parseExpression( )

      # EOF
      if self._scanner.peekToken( ) not in ( PuckScanner.EOF_TOK, PuckScanner.SEMI_COLON_TOK ):
         raise ParseError( self._scanner, 'EOF or \';\' Expected.' )

      self._scanner.consume( )

      return pkExprObj

   def _parseExpression( self ):
      # Receiver
      receiverObj = self._parseObject( )
      if receiverObj is None:
         return None

      # Message
      if self._scanner.peekToken( ) not in ( PuckScanner.SEMI_COLON_TOK, PuckScanner.CLOSE_BRACKET_TOK, PuckScanner.EOF_TOK ):
         return self._parseMessage( receiverObj )
      else:
         return receiverObj

   def _parseObject( self ):
      nextToken = self._scanner.peekToken( )
      if nextToken == PuckScanner.INTEGER_TOK:
         lex = self._scanner.getLexeme( )
         lexVal = int(lex)
         theObj = PuckImpl.PkObject( PuckImpl.pkNumberClass, lexVal )
         self._scanner.consume( )
      elif nextToken== PuckScanner.FLOAT_TOK:
         lex = self._scanner.getLexeme( )
         lexVal = float(lex)
         theObj = PuckImpl.PkObject( PuckImpl.pkNumberClass, lexVal )
         self._scanner.consume( )
      elif nextToken == PuckScanner.STRING_TOK:
         lex = self._scanner.getLexeme( )
         theObj = PuckImpl.PkObject( PuckImpl.pkStringClass, lex[1:-1] )
         self._scanner.consume( )
      elif nextToken == PuckScanner.SYMBOL_TOK:
         lex = self._scanner.getLexeme( )
         theObj = PuckImpl.PkObject( PuckImpl.pkSymbolClass, lex )
         self._scanner.consume( )
      elif nextToken == PuckScanner.POUND_SIGN_TOK:
         self._scanner.consume( )
         quotedObj = self._parseObject( )
         theObj = PuckImpl.PkObject( PuckImpl.pkQuoteClass, quotedObj )
      elif nextToken == PuckScanner.OPEN_BRACKET_TOK:
         theObj = self._parseList( )
      else:
         raise ParseError( self._scanner, 'Object expected.' )

      nextToken = self._scanner.peekToken( )
      while nextToken == PuckScanner.POUND_SIGN_TOK:
         # We may have a use of shorthand-#
         self._scanner.consume( )
         if self._scanner.peekToken( ) != PuckScanner.SYMBOL_TOK:
            raise ParseError( self._scanner, 'Symbol expected after shorthand-#' )
         lex = self._scanner.getLexeme( )
         self._scanner.consume( )

         sym = PuckImpl.PkObject( PuckImpl.pkSymbolClass, lex )
         theExpr = PuckImpl.makePkExpr( [ 'member:' ], [ theObj, PuckImpl.PkObject(PuckImpl.pkQuoteClass, sym) ] )
         theObj = PuckImpl.makePkList( [ theExpr ], PuckImpl.PkEnvironment(self._currentEnv) )

         nextToken = self._scanner.peekToken( )

      return theObj

   def _parseMessage( self, receiverObj ):
      aKeyList  = [ ]
      anArgList = [ receiverObj ]

      # Parse a key
      if self._scanner.peekToken( ) != PuckScanner.SYMBOL_TOK:
         raise ParseError( self._scanner, 'Symbol expected.' )

      key = self._scanner.getLexeme()
      aKeyList.append( self._scanner.getLexeme() )
      self._scanner.consume( )

      # Parse argument & keys
      if self._scanner.peekToken( ) not in ( PuckScanner.SEMI_COLON_TOK, PuckScanner.CLOSE_BRACKET_TOK, PuckScanner.EOF_TOK ):
         # Parse an argument
         anArgList.append( self._parseObject( ) )

         while self._scanner.peekToken( ) == PuckScanner.SYMBOL_TOK:
            # Parse keys
            aKeyList.append( self._scanner.getLexeme() )
            self._scanner.consume( )

            # Parse arguments
            anArgList.append( self._parseObject() )

      return PuckImpl.makePkExpr( aKeyList, anArgList )

   def _parseList( self ):
      # Open Bracket
      if self._scanner.peekToken() != PuckScanner.OPEN_BRACKET_TOK:
         raise ParseError( self._scanner, "'[' Expected." )

      # Begin a lexical scope
      self._currentEnv = PuckImpl.PkEnvironment( self._currentEnv )

      self._scanner.consume( )

      # Parameters and Locals
      params = [ ]
      allLocals = [ ]    # all locals: params and local scope temporaries
      if self._scanner.peekToken( ) == PuckScanner.PIPE_TOK:
         self._scanner.consume( )
         
         nextToken = self._scanner.peekToken( )
         while nextToken in (PuckScanner.COLON_TOK, PuckScanner.SYMBOL_TOK):
            isParam = False
            if nextToken == PuckScanner.COLON_TOK:
               isParam = True
               self._scanner.consume( )
         
            if self._scanner.peekToken( ) != PuckScanner.SYMBOL_TOK:
               raise ParseError( self._scanner, "Symbol expected." )
            sym = self._scanner.getLexeme( )
            if isParam:
               params.append( sym )
            allLocals.append( sym )
            self._scanner.consume( )
         
            nextToken = self._scanner.peekToken( )
      
         if self._scanner.peekToken() != PuckScanner.PIPE_TOK:
            raise ParseError( self._scanner, "'|' expected." )
         self._scanner.consume( )
      
      # Expressions
      expressions = [ ]
      if self._scanner.peekToken() != PuckScanner.CLOSE_BRACKET_TOK:
         expr = self._parseExpression( )
         if expr is not None:
            expressions.append( expr )

         while self._scanner.peekToken() != PuckScanner.CLOSE_BRACKET_TOK:
            # Semi Colon
            if self._scanner.peekToken( ) != PuckScanner.SEMI_COLON_TOK:
               raise ParseError( self._scanner, "';' expected." )

            self._scanner.consume( )

            expr = self._parseExpression( )
            if expr is not None:
               expressions.append( expr )

      # Close Bracket
      if self._scanner.peekToken( ) != PuckScanner.CLOSE_BRACKET_TOK:
         raise ParseError( self._scanner, "']' expected." )

      self._scanner.consume( )

      result = PuckImpl.makePkList( expressions, self._currentEnv, params, allLocals )

      # Close a Lexical scope
      self._currentEnv = self._currentEnv.parentEnv( )

      return result


def parseAndPrintExpr( anExpr ):
   try:
      puck = PuckParser( PuckImpl.GLOBAL )
      result = puck.parse( anExpr )
      resultStr = PuckImpl.printable( result )
      print( resultStr )
   except ParseError as ex:
      print( ex.generateVerboseErrorString() )
   except PuckImpl.PuckException as ex:
      print( ex )
   except Exception as ex:
      print( ex )

def parseEvalAndPrintExpr( anExpr ):
   puck = PuckParser( PuckImpl.GLOBAL )
   expr = puck.parse( anExpr )
   result = PuckImpl.EVAL_OBJ_R( expr, PuckImpl.GLOBAL )
   resultStr = PuckImpl.printable( result )
   print( resultStr )

def test( anExpr ):
   print( '\n>>> ', anExpr )
   parseEvalAndPrintExpr( anExpr )

if __name__ == '__main__':
   test( '''Date <- [Object make]''' )
   test( '''Date member: #name setTo: "Date"''' )
   test( '''Date member: #init setTo:
               #[ | self |
               self member: #year  setTo: 2013;
               self member: #month setTo:    1;
               self member: #day   setTo:    1
               ]''' )
   test( '''aDate <- [ Date make ]''' )
   aDate = PuckImpl.GLOBAL.get( 'aDate' )
   test( '''aDate init''' )
   test( '''aDate listMembers''' )
   #test( '''Date member: #addYears: setTo:
               ##[ | self numYears |
               #"self --" printValue;
               #self printMembers;

               #"" printValue;
               #"self#year --" printValue;
               #"   VALUE" printValue;
               #[self#year] printValue;
               #"   MEMBERS" printValue;
               #[self#year] printMembers;

               #"" printValue;
               #"[self member: #year] --" printValue;
               #"   VALUE" printValue;
               #[self member: #year] printValue;
               #"   MEMBER" printValue;
               #[self member: #year] printMembers;

               #"" printValue;
               #"null --" printValue;
               #"   VALUE" printValue;
               #null printValue;
               #"   MEMBERS" printValue;
               #null printMembers;

               #"" printValue;
               #"[self#year] is null :::" printValue;
               #[[self#year] = null] printValue;
               #self member: #year setTo: [self#year + numYears]
               #]''' )
   test( '''Date member: #addYears: setTo:
               #[ | self numYears |
               self member: #year setTo: [self#year + numYears]
               ]''' )
   test( '''aDate member: #year setTo: 2013''' )
   test( '''aDate addYears: 1''' )
   test( '''aDate#year''' )
