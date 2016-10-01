import Scanner
from Scanner import ParseError, ScannerState


class PuckScanner( Scanner.Scanner ):
   WHITESPACE     = ' \t\n\r'
   SIGN           = '+-'
   DIGIT          = '0123456789'
   SIGN_OR_DIGIT  = SIGN + DIGIT
   ALPHA_LOWER    = 'abcdefghijklmnopqrstuvwxyz'
   ALPHA_UPPER    = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
   ALPHA          = ALPHA_LOWER + ALPHA_UPPER
   SYMBOL_OTHER   = '~!@$%^&*_=\/?<>'
   SYMBOL_FIRST   = ALPHA + SIGN + SYMBOL_OTHER
   SYMBOL_REST    = ALPHA + SIGN + SYMBOL_OTHER + DIGIT + ':'

   EOF_TOK            =   0

   SYMBOL_TOK         = 101    # Value Objects
   STRING_TOK         = 102
   INTEGER_TOK        = 111
   FLOAT_TOK          = 112

   OPEN_BRACKET_TOK   = 201    # Paired Symbols
   CLOSE_BRACKET_TOK  = 202
   OPEN_PAREN_TOK     = 211
   CLOSE_PAREN_TOK    = 212

   SEMI_COLON_TOK     = 500    # Other Symbols
   POUND_SIGN_TOK     = 501
   PIPE_TOK           = 502
   COLON_TOK          = 503

   def __init__( self, ):
      Scanner.Scanner.__init__( self )

   def tokenize( self, aString, EOFToken=0 ):
      try:
         tokenList = super().tokenize( aString, EOFToken )

         for tokLexPair in tokenList:
            print( '{0:<4} /{1}/'.format( *tokLexPair ) )

      except ParseError as ex:
         print( ex.errorString(verbose=True) )

      except Exception as ex:
         print( ex )

   def _scanNextToken( self ):
      try:
         self._skipWhitespaceAndComments( )

         nextChar = self.buffer.peek( )
         if nextChar is None:
            return PuckScanner.EOF_TOK
         if nextChar == '[':
            self.buffer.markStartOfLexeme( )
            self.buffer.consume( )
            return PuckScanner.OPEN_BRACKET_TOK
         elif nextChar == ']':
            self.buffer.markStartOfLexeme( )
            self.buffer.consume( )
            return PuckScanner.CLOSE_BRACKET_TOK
         elif nextChar == '(':
            self.buffer.markStartOfLexeme( )
            self.buffer.consume( )
            return PuckScanner.OPEN_PAREN_TOK
         elif nextChar == ')':
            self.buffer.markStartOfLexeme( )
            self.buffer.consume( )
            return PuckScanner.CLOSE_PAREN_TOK
         elif nextChar == ';':
            self.buffer.markStartOfLexeme( )
            self.buffer.consume( )
            return PuckScanner.SEMI_COLON_TOK
         elif nextChar == '#':
            self.buffer.markStartOfLexeme( )
            self.buffer.consume( )
            return PuckScanner.POUND_SIGN_TOK
         elif nextChar == '|':
            self.buffer.markStartOfLexeme( )
            self.buffer.consume( )
            return PuckScanner.PIPE_TOK
         elif nextChar == ':':
            self.buffer.markStartOfLexeme( )
            self.buffer.consume( )
            nextChar = self.buffer.peek( )
            return PuckScanner.COLON_TOK
         elif nextChar == '"':
            return self._scanStringLiteral( )
         elif nextChar in PuckScanner.SIGN_OR_DIGIT:
            return self._scanNumOrSymbol( )
         elif nextChar in PuckScanner.SYMBOL_FIRST:
            return self._scanSymbol( )
         else:
            raise ParseError( self, 'Unknown Token' )

      except ParseError:
         raise

      except:
         #print( 'Unknown parsing error, assuming EOF' )
         return PuckScanner.EOF_TOK

   def _scanStringLiteral( self ):
      nextChar = self.buffer.peek( )
      if nextChar != '"':
         raise ParseError( self, '\'"\' expected.' )
      self.buffer.markStartOfLexeme( )
      self.buffer.consume( )
      self.buffer.consumeUpTo( '"' )
      self.buffer.consume( )

      return PuckScanner.STRING_TOK

   def _scanNumOrSymbol( self ):
      SAVE = ScannerState( )
      nextChar = self.buffer.peek( )

      self.buffer.markStartOfLexeme( )
      self.saveState( SAVE )                  # Save the scanner state

      self.buffer.consume( )

      if nextChar in PuckScanner.SIGN:
         secondChar = self.buffer.peek( )
         if (secondChar is None) or (secondChar not in PuckScanner.DIGIT):
            self.restoreState( SAVE )         # Restore the scanner state
            return self._scanSymbol( )

      self.buffer.consumePast( PuckScanner.DIGIT )

      if self.buffer.peek() == '.':
         # Possibly a floating point number
         self.saveState( SAVE )
         self.buffer.consume()
         if self.buffer.peek() not in PuckScanner.DIGIT:
            # Integer
            self.restoreState( SAVE )
         else:
            self.buffer.consumePast( PuckScanner.DIGIT )
         return PuckScanner.FLOAT_TOK

      return PuckScanner.INTEGER_TOK

   def _scanSymbol( self ):
      self.buffer.markStartOfLexeme( )
      nextChar = self.buffer.peek()
      if nextChar not in PuckScanner.SYMBOL_FIRST:
         raise ParseError( self, 'Invalid symbol character' )
      self.buffer.consume( )

      self.buffer.consumePast( PuckScanner.SYMBOL_REST )

      return PuckScanner.SYMBOL_TOK

   def _skipWhitespaceAndComments( self ):
      SAVE = ScannerState( )

      while self.buffer.peek() in '; \t\n\r':
         self.buffer.consumePast( ' \t\n\r' )

         if self.buffer.peek() == ';':
            self.saveState( SAVE )
            self.buffer.consume()
            if self.buffer.peek() == ';':
               self.buffer.consumeUpTo( '\n\r' )
            else:
               self.restoreState( SAVE )
               return


if __name__ == '__main__':
   scn = PuckScanner( )
   scn.tokenize( '' )
