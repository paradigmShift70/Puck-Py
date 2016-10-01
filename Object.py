# ################################
# Define the Execution Environment

class PkEnvironment( object ):
   SAVE = [ ]

   def __init__( self, aParentEnvironment=None ):
      self._parentEnvironment  = aParentEnvironment
      self._symbolTable        = { }

   def parentEnv( self ):
      return self._parentEnvironment

   def resetLocal( self ):
      self._symbolTable        = { }

   def declLocal( self, aSymbol, aValue=None ):
      self._symbolTable[ aSymbol ] = aValue

   def set( self, aSymbol, aValue ):
      self._set( aSymbol, aValue, self )

   def get( self, aSymbol ):
      if aSymbol in self._symbolTable:
         return self._symbolTable[ aSymbol ]
      elif self._parentEnvironment is None:
         return None
      else:
         return self._parentEnvironment.get( aSymbol )

   def _set( self, aSymbol, aValue, localScope ):
      if aSymbol in self._symbolTable:
         self._symbolTable[ aSymbol ] = aValue
      elif self._parentEnvironment is None:
         localScope.declLocal( aSymbol, aValue )
      else:
         self._parentEnvironment._set( aSymbol, aValue, localScope )

   def isDefined( self, aSymbol ):
      if aSymbol in self._symbolTable:
         return True
      elif self._parentEnvironment is None:
         return False
      else:
         return self._parentEnvironment.isDefined( aSymbol )

   def saveSymTab( self ):
      PkEnvironment.SAVE.append( self._symbolTable.copy() )

   def restoreSymTab( self ):
      self._symbolTable = PkEnvironment.SAVE.pop( )

GLOBAL = PkEnvironment( )

class PkEvaluationStack( object ):
   def __init__( self ):
      self._stk = [ ]

   def push( self, obj ):
      self._stk.append( obj )

   def pushMulti( self, *objs ):
      self._stk.extend( objs )

   def pop( self ):
      return self._stk.pop( )

   def popMulti( self, numToPop=2 ):
      result = self._stk[ 0 - numToPop : ]
      del self._stk[ 0 - numToPop : ]
      result.reverse()
      return result

   def top( self, offset=0 ):
      return self._stk[ -1 - offset ]

   def topMulti( self, numToGet ):
      result = self._stk[ 0 - numToGet : ]
      result.reverse()
      return result

   def topSetTo( self, offset, newValue ):
      self._stk[ -1 - offset ] = newValue

   def removeMulti( self, numToRemove=1 ):
      del self._stk[ 0 - numToRemove : ]

   def popAndTestArgs( self, anArgCount, *typeList ):
      if anArgCount != len(typeList):
         raise PuckException( "Exactly {0} arguments expected.".format( len(typeList) ) )

      anArgList = self.popMulti( anArgCount )

      failedOnArg = -1
      for argNum, argPair in enumerate(zip( anArgList, typeList )):
         argObj, argType = argPair
         if isinstance( argType, str ):
            soughtPkObj = GLOBAL.get( argType )

            traversePoint = argObj._class
            while (traversePoint != soughtPkObj) and (traversePoint != pkObjectClass):
               traversePoint = traversePoint._class

            if traversePoint != soughtPkObj:
               raise PuckException( "Argument {0} expected to be a {1}.".format( argNum, argType ) )

         elif argType is None:
            pass

         else:
            raise PuckException( "Argument {0} expecte to be a {1}.".format( argNum, argType ) )

      if anArgCount == 1:
         return anArgList[0]
      else:
         return anArgList

   def testArgs( self, anArgCount, *typeList ):
      if anArgCount != len(typeList):
         raise PuckException( "Exactly {0} arguments expected.".format( len(typeList) ) )

      anArgList = self.topMulti( anArgCount )

      failedOnArg = -1
      for argNum, argPair in enumerate(zip( anArgList, typeList )):
         argObj, argType = argPair
         if isinstance( argType, str ):
            soughtPkObj = GLOBAL.get( argType )

            traversePoint = argObj._class
            while (traversePoint != soughtPkObj) and (traversePoint != pkObjectClass):
               traversePoint = traversePoint._class

            if traversePoint != soughtPkObj:
               raise PuckException( "Argument {0} expecte to be a {1}.".format( argNum, argType ) )

         elif argType is None:
            pass

         else:
            raise PuckException( "Argument {0} expecte to be a {1}.".format( argNum, argType ) )


STACK  = PkEvaluationStack( )

class PuckException( Exception ):
   def __init__( self, aMessage="" ):
      self._message = aMessage
   def __str__( self ):
      return self._message

# #############################################
# Define the Fundamental Implementation Objects

class PkObject( object ):
   def __init__( self, aPkClass=None, value=None, **kwds ):
      self._value     = value
      self._class     = aPkClass if aPkClass else self

      self._members = { }                     # Keys are python str, values are Puck Object Instances
      self._members[ 'class' ] = self._class
      self._members[ 'self'  ] = self
      self._members.update( kwds )

   def findMember( self, aMemberName ):
      '''searches this and all objects up the class tree until aMemberName
      is found.  If not found an Exception is thrown.

      Note:  Non-recursive to assist performance.
      '''
      theObjToSearch = self
      while True:
         theMbr = theObjToSearch._members.get( aMemberName )
         if theMbr is not None:
            return theMbr
         elif theObjToSearch._class is theObjToSearch:
            raise PuckException( 'Invalid member name {0}.'.format( aMemberName ) )
         else:
            theObjToSearch = theObjToSearch._class

def printableID( anObj ):
   try:
      name = anObj._members[ 'name' ]._value
   except:
      name = ''

   primitiveAugmentStr = ' Primitive' if anObj._class is GLOBAL.get('Primitive') else ''
   nameAugmentStr      = ' name=\"{0}\"'.format( name ) if name != '' else ''

   return '<object{0} id={1}{2}>'.format( primitiveAugmentStr, id(anObj), nameAugmentStr )

def printable( anObj ):
   def isInstanceOf( anObj, classNameStr ):
      EVAL_EXPR( anObj, 'isKindOf:', [ GLOBAL.get(classNameStr) ], GLOBAL )
      result = STACK.pop( )
      #result = EVAL_EXPR_R( anObj, 'isKindOf:', [ GLOBAL.get(classNameStr) ], GLOBAL )
      return result is GLOBAL.get('true')

   if anObj is None:
      return None

   elif (anObj._value is not None) and (not isInstanceOf( anObj, 'Primitive' )):
      # We have an instance of a primitive object
      if isInstanceOf( anObj, 'Number' ):
         return str( anObj._value )

      elif isInstanceOf( anObj, 'Symbol' ):
         return str( anObj._value )

      elif isInstanceOf( anObj, 'String' ):
         return '"' + str( anObj._value ) + '"'

      elif isInstanceOf( anObj, 'Null' ):
         return 'null'

      elif isInstanceOf( anObj, 'Boolean' ):
         return 'true' if anObj._value else 'false'

      elif isInstanceOf( anObj, 'Quote' ):
         return '#' + printable(anObj._value)

      elif isInstanceOf( anObj, 'List' ):
         # Assemble Params & Locals
         paramsAndLocals = [ ]
         for sym in anObj._members['allLocals']:
            if sym in anObj._members['parameters']:
               paramsAndLocals.append( ':' + sym )
            else:
               paramsAndLocals.append( sym )
         
         paramStr = ' '.join( paramsAndLocals )

         # Assemble Expressions (Item List)
         exprStr  = '; '.join( [ printable(expr) for expr in anObj._value ] )

         # Construct the complete string
         if paramStr != '':
            paramStr = ' | ' + paramStr + ' |'

         return '[' + paramStr + ' ' + exprStr + ' ]'

      elif isInstanceOf( anObj, 'Expression' ):
         msgString = ''

         if len(anObj._args) == 1:
            msgString = ' ' + anObj._keyList[0]
         else:
            for key,val in zip( anObj._keyList, anObj._args[1:] ):
               msgString += ' ' + key + ' ' + printable(val)
         return '{0}{1}'.format(printable(anObj._args[0]), msgString)

   elif isInstanceOf( anObj, 'Object' ):
      # We have Primitive, built-in Class, user-defined class or instance of a user-defined class.
      return printableID( anObj )

   return '### UNKNOWN ###'

# #######################################
# Define the Python Implementation Classes
def EVAL_OBJ_R( anObj, anEnv=GLOBAL, isLValue=False ):
   EVAL_EXPR( anObj, 'eval', [ ], anEnv, isLValue )
   return STACK.pop()

def EVAL_EXPR( anObj, aSel, anArgList=[], anEnv=GLOBAL, isLValue=False ):
   numArgs = 0
   if anArgList and (len(anArgList) > 0):
      argListCopy = anArgList[:]
      argListCopy.reverse()
      STACK.pushMulti( *argListCopy )
      numArgs = len(argListCopy)
   STACK.push( anObj )
   STACK_EVAL( aSel, numArgs+1, anEnv, isLValue )

def STACK_EVAL( aSel, anArgCt, anEnv=GLOBAL, isLValue=False ):
   try:
      theHandler = STACK.top().findMember( aSel )   # throws if aSel not found
   except:
      print( 'Throwing' )
      print( '   Object: ', printable(STACK.top()) )
      print( )
      raise

   if theHandler._class is pkListClass:
      theArgList = STACK.popMulti( anArgCt )
      theArgsPkList = makePkList( theArgList, anEnv )
      STACK.pushMulti( theArgsPkList, theHandler )
      #STACK_EVAL( 'evalForArgs:', 2, anEnv, isLValue )
      theHandler = GLOBAL.get( 'listEvalForArgs' )
      theHandler._value( anEnv, 2, isLValue )
   else:
      theHandler._value( anEnv, anArgCt, isLValue )

# ##########################
# Define the Puck Primitives

# pkObject Operations
def ppImpl_Object_sameObjectAs_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Object', 'Object' )

   if receiver is arg1:
      STACK.push( GLOBAL.get('true') )
   else:
      STACK.push( GLOBAL.get('false') )

def ppImpl_Object_isKindOf_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Object', 'Object' )

   while (receiver._class is not arg1) and (receiver._class is not receiver):
      receiver = receiver._class

   if receiver._class == arg1:
      STACK.push( GLOBAL.get('true') )
   else:
      STACK.push( GLOBAL.get('false') )

def ppImpl_Object_equalTo_( anEnv, anArgCt, isLValue=False ):
   try:
      receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Object', 'Object' )
   except:
      STACK.push( GLOBAL.get('false'))
      return

   EVAL_EXPR( receiver, 'compareTo:', [ arg1 ], anEnv, isLValue )
   result = STACK.pop( )
   if (result._class == pkNumberClass) and (result._value == 0):
      STACK.push( GLOBAL.get('true') )
   else:
      STACK.push( GLOBAL.get('false') )

def ppImpl_Object_notEqualTo_( anEnv, anArgCt, isLValue=False ):
   try:
      receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Object', 'Object' )
   except:
      STACK.push( GLOBAL.get('false'))
      return

   EVAL_EXPR( receiver, 'compareTo:', [ arg1 ], anEnv, isLValue )
   result = STACK.pop( )
   if (result._class == pkNumberClass) and (result._value != 0):
      STACK.push( GLOBAL.get('true') )
   else:
      STACK.push( GLOBAL.get('false') )

def ppImpl_Object_compareTo_( anEnv, anArgCt, isLValue=False ):
   try:
      receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Object', 'Object' )
   except:
      STACK.push( GLOBAL.get('false'))
      return

   STACK.push( makePkNumber(0 if (receiver._value == arg1._value) and (receiver._class == arg1._class) else -1) )

def ppImpl_Object_eval( anEnv, anArgCt, isLValue=False ):
   pass # return the receiver, which is already at the top of the stack.

def ppImpl_Object_evalMessage_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Object', 'List' )

   theArgs     = arg1[0]._value
   theSelStr   = theArgs[0]

   if len(theArgs) > 1:
      EVAL_EXPR( receiver, theSelStr, theArgs[1:], anEnv, isLValue )
   else:
      EVAL_EXPR( receiver, theSelStr, [ ], anEnv, isLValue )

def ppImpl_Object_member_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Object', 'Symbol' )

   try:
      theValue = receiver.findMember( arg1._value )
      if theValue is None:
         theValue = GLOBAL.get('null')
   except:
      theValue = GLOBAL.get('null')

   STACK.push( theValue )

def ppImpl_Object_memberRemove_( anEnv, anArgCt, isLValue=False ):
   raise PuckException( "Object#memberRemove: not yet implemented." )
   # need to implement this.  Return true if the member is in
   # the object and gets deleted.  Otherwise return false.

def ppImpl_Object_member_setTo_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1, arg2 = STACK.popAndTestArgs( anArgCt, 'Object', 'Symbol', 'Object' )

   theSoughtSymStr = arg1._value

   # Locate the object in which to set named member
   theObjToModify = receiver
   while True:
      if theSoughtSymStr in theObjToModify._members:
         break
      elif theObjToModify._class is theObjToModify:
         theObjToModify = receiver
         break
      else:
         theObjToModify = theObjToModify._class

   # Set the named member
   theObjToModify._members[ theSoughtSymStr ] = arg2
   STACK.push( arg2 )

def ppImpl_Object_selfMember_setTo_( anEnv, anArgCt, isLvalue=False ):
   receiver, arg1, arg2 = STACK.popAndTestArgs( anArgCt, 'Object', 'Symbol', 'Object' )
   receiver._members[ arg1._value ] = arg2
   STACK.push( arg2 )

def ppImpl_Object_memberList( anEnv, anArgCt,isLValue=False ):
   receiver = STACK.pop( )
   memberStrings = sorted( receiver._members.keys() )
   members = [ PkObject(pkSymbolClass, mem) for mem in memberStrings ]
   thePkListOfMembers = makePkList( members, anEnv )
   STACK.push( thePkListOfMembers )

def ppImpl_Object_make( anEnv, anArgCt, isLValue=False ):
   receiver = STACK.pop( )
   thePkInstance = PkObject( receiver )
   STACK.push( thePkInstance )

def ppImpl_Object_delete( anEnv, anArgCt, isLValue=False ):
   pass

def ppImpl_Object_printValue( anEnv, anArgCt, isLValue=False ):
   STACK.testArgs( 1, "Object" )
   receiver = STACK.top( )
   try:
      print( receiver._value )
   except:
      pass

def ppImpl_Object_printMembers( anEnv, anArgCt, isLValue=False ):
   receiver = STACK.top( )
   for mbr, val in receiver._members.items():
      print( 'Member: ', mbr )
      print( '   ', printable( val ) )

# pkPrimitive Operations
def ppImpl_Primitive_evalForArgs_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Primitive', 'List' )

   theArgsList = arg1._value[:]
   theArgsList.reverse()
   for item in theArgsList:
      EVAL_EXPR( item, 'eval', [ ], anEnv, isLValue )

   return receiver._value( anEnv, len(arg1._value) )

# pkNull Operations
#   none defined
# pkBoolean Operations
def ppImpl_Boolean_negation( anEnv, anArgCt, isLValue=False ):
   receiver = STACK.popAndTestArgs( anArgCt, 'Boolean' )

   if receiver._value:
      STACK.push( GLOBAL.get('false') )
   else:
      STACK.push( GLOBAL.get('true') )

def ppImpl_Boolean_and_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Boolean', 'Boolean' )

   if receiver._value and arg1._value:
      STACK.push( GLOBAL.get('true') )
   else:
      STACK.push( GLOBAL.get('false') )

def ppImpl_Boolean_or_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Boolean', 'Boolean' )

   if receiver._value or arg1._value:
      STACK.push( GLOBAL.get('true') )
   else:
      STACK.push( GLOBAL.get('false') )

def ppImpl_Boolean_ifTrue_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Boolean', 'Object' )

   if receiver is GLOBAL.get('true'):
      EVAL_EXPR( arg1, 'eval', [ ], anEnv, isLValue )
   else:
      STACK.push( GLOBAL.get( 'null' ) )

def ppImpl_Boolean_ifTrue_ifFalse_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1, arg2 = STACK.popAndTestArgs( anArgCt, 'Boolean', 'Object', 'Object' )

   if receiver is GLOBAL.get('true'):
      EVAL_EXPR( arg1, 'eval', [ ], anEnv, isLValue )
   else:
      EVAL_EXPR( arg2, 'eval', [ ], anEnv, isLValue )

# pkMagnitude Operations
def ppImpl_Magnitude_lessThan_( anEnv, anArgCt, isLValue=False ):
   try:
      receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Magnitude', 'Magnitude' )
   except:
      STACK.push( GLOBAL.get('false'))
      return

   EVAL_EXPR( receiver, 'compareTo:', [ arg1 ], anEnv, isLValue )
   result = STACK.pop( )
   if result._value < 0:
      STACK.push( GLOBAL.get('true') )
   else:
      STACK.push( GLOBAL.get('false') )

def ppImpl_Magnitude_lessThanOrEqualTo_( anEnv, anArgCt, isLValue=False ):
   try:
      receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Magnitude', 'Magnitude' )
   except:
      STACK.push( GLOBAL.get('false'))
      return

   EVAL_EXPR( receiver, 'compareTo:', [ arg1 ], anEnv, isLValue )
   result = STACK.pop( )
   if result._value <= 0:
      STACK.push( GLOBAL.get('true') )
   else:
      STACK.push( GLOBAL.get('false') )

def ppImpl_Magnitude_greaterThan_( anEnv, anArgCt, isLValue=False ):
   try:
      receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Magnitude', 'Magnitude' )
   except:
      STACK.push( GLOBAL.get('false'))
      return

   EVAL_EXPR( receiver, 'compareTo:', [ arg1 ], anEnv, isLValue )
   result = STACK.pop( )
   if result._value > 0:
      STACK.push( GLOBAL.get('true') )
   else:
      STACK.push( GLOBAL.get('false') )

def ppImpl_Magnitude_greaterThanOrEqualTo_( anEnv, anArgCt, isLValue=False ):
   try:
      receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Magnitude', 'Magnitude' )
   except:
      STACK.push( GLOBAL.get('false'))
      return

   EVAL_EXPR( receiver, 'compareTo:', [ arg1 ], anEnv, isLValue )
   result = STACK.pop( )
   if result._value >= 0:
      STACK.push( GLOBAL.get('true') )
   else:
      STACK.push( GLOBAL.get('false') )

# pkString Operations
def ppImpl_String_compareTo_( anEnv, anArgCt, isLValue=False ):
   try:
      receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'String', 'String' )
   except:
      STACK.push( GLOBAL.get('false') )
      return

   if receiver._value < arg1._value:
      result = -1
   elif receiver._value == arg1._value:
      result = 0
   else:
      result = 1

   STACK.push( makePkNumber(result) )

def ppImpl_String_length( anEnv, anArgCt, isLValue=False ):
   receiver = STACK.popAndTestArgs( anArgCt, 'String' )
   STACK.push( PkObject( pkNumberClass, len(receiver._value) ) )

def ppImpl_String_at_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'String', 'Number' )
   STACK.push( PkObject(pkStringClass,receiver._value[arg1._value]) )

def ppImpl_String_from_to_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1, arg2 = STACK.popAndTestArgs( anArgCt, 'String', 'Number', 'Number' )
   STACK.push( PkObject(pkStringClass,receiver._value[ arg1._value : arg2._value ]) )

def ppImpl_String_add_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'String', 'String' )
   STACK.push( PkObject(pkStringClass,receiver._value + arg1._value) )

def ppImpl_String_forEachCharacter_( anEnv, anArgCt, isLValue=False ):
   raise PuckException( "String#forEachCharacter: not yet implemented." )

def ppImpl_String_parsePuckExpr( anEnv, anArgCt, isLValue=False ):
   raise PuckException( "String#parsePuckExpr not yet implemented." )

# pkNumber Operations
def ppImpl_Number_compareTo_( anEnv, anArgCt, isLValue=False ):
   try:
      receiver, arg1 = STACK.popAndTestArgs(anArgCt, 'Number', 'Number')
   except:
      STACK.push( GLOBAL.get('false') )
      return

   delta = receiver._value - arg1._value
   STACK.push( makePkNumber(delta) )

def ppImpl_Number_add_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Number', 'Number' )
   STACK.push( PkObject( pkNumberClass, receiver._value + arg1._value ) )

def ppImpl_Number_sub_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Number', 'Number' )
   STACK.push( PkObject( pkNumberClass, receiver._value - arg1._value ) )

def ppImpl_Number_mul_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Number', 'Number' )
   STACK.push( PkObject( pkNumberClass, receiver._value * arg1._value ) )

def ppImpl_Number_div_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Number', 'Number' )
   STACK.push( PkObject( pkNumberClass, receiver._value / arg1._value ) )

def ppImpl_Number_pow_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Number', 'Number' )

   powVal = receiver._value ** arg1._value
   STACK.push( makePkNumber(powVal) )

def ppImpl_Number_truncate( anEnv, anArgCt, isLValue=False ):
   receiver = STACK.popAndTestArgs( anArgCt, 'Number' )
   STACK.push( PkObject( pkNumberClass, int(receiver._value) ) )

def ppImpl_Number_doTimes_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'Number', 'Object' )
   for count in range( 0, receiver._value ):
      EVAL_EXPR( arg1, 'evalForArgs:',
                 [ makePkList( [PkObject(pkNumberClass,count)], anEnv)
                 ],
                 anEnv,
                 isLValue )
      mostRecent = STACK.pop( )
   STACK.push( mostRecent )

# pkQuote Operations
def ppImpl_Quote_eval( anEnv, anArgCt, isLValue=False ):
   receiver = STACK.popAndTestArgs( anArgCt, 'Quote' )
   STACK.push( receiver._value )

# pkSymbol Operations
def ppImpl_Symbol_eval( anEnv, anArgCt, isLValue=False ):
   STACK.testArgs( anArgCt, 'Symbol' )
   receiver = STACK.top()

   if not isLValue:
      val = anEnv.get( receiver._value )
      if val is not None:
         STACK.topSetTo(0, val)  # return the valuation of the symbol
   #Otherwise, the PkSymbolInst is at the top of stack.  Leave it as the ret val.

def ppImpl_Symbol_assign_( anEnv, anArgCt, isLValue=False ):
   STACK.testArgs( anArgCt, 'Symbol', 'Object' )
   receiver = STACK.pop()
   theValue        = STACK.top() # leave it as the return value
   anEnv.set( receiver._value, theValue )

# pkList Operations
def ppImpl_List_eval( anEnv, anArgCt, isLValue=False ):
   receiver = STACK.popAndTestArgs( anArgCt, 'List' )

   # Save the state of the prior call to this fn
   receiver._environment.saveSymTab( )

   # Initialize the new symbol table
   for symStr in receiver._members['allLocals']:
      receiver._environment.declLocal( symStr, GLOBAL.get('null') )
   
   # Evaluate the items each in turn
   for thePkObj in receiver._value:
      mostRecent = EVAL_OBJ_R( thePkObj, receiver._environment, isLValue )

   # Restore the state of the prior call to this fn
   receiver._environment.restoreSymTab( )

   STACK.push( mostRecent )

def ppImpl_List_evalForArgs_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'List', 'List' )
   # thePkListInst is the list itself.  arg1 is the list of args passed to evalForArgs:

   # Save the state of the prior call to this fn
   receiver._environment.saveSymTab( )

   # Initialize the new symbol table
   for symStr in receiver._members['allLocals']:
      receiver._environment.declLocal( symStr, GLOBAL.get('null') )
   
   # In reverse order push each arg, evaluate it, and assign the result to its respective param.
   theArgList   = arg1._value
   theParamList = receiver._members[ 'parameters' ]
   initLocal    = receiver._environment.declLocal
   numArgs      = len(theArgList)
   if numArgs != len(theParamList):
      raise PuckException( 'Invalid number of arguments ({0}) passed to a list.  {1} expected.'.format(numArgs,len(theParamList)) )
   for argNum in range(numArgs-1, -1, -1):
      STACK.push( theArgList[argNum] )
      STACK_EVAL( 'eval', 1, anEnv )
      initLocal( theParamList[argNum], STACK.top() )

   # Now evaluate the elements in the list.
   for thePkObj in receiver._value:
      mostRecent = EVAL_OBJ_R( thePkObj, receiver._environment, False )

   # Remove the arguments, then push the return value
   STACK.removeMulti( numArgs )

   # Restore the state of the prior call to this fn
   receiver._environment.restoreSymTab( )

   STACK.push( mostRecent )

def ppImpl_List_evalInPlace( anEnv, anArgCt, isLValue=False ):
   receiver = STACK.popAndTestArgs( 1, 'List' )

   # Save the state of the prior call to this fn
   receiver._environment.saveSymTab( )

   # Initialize the new symbol table
   for symStr in receiver._members['allLocals']:
      receiver._environment.declLocal( symStr, GLOBAL.get('null') )
   
   theNewList = [ ]
   for element in receiver._value:
      STACK.push( element )
      STACK_EVAL( 'eval', 1, anEnv )
      evaluatedElement = STACK.pop( )
      theNewList.append( evaluatedElement )

   STACK.push( makePkList( theNewList, PkEnvironment(anEnv.parentEnv()) ) )

   # Restore the state of the prior call to this fn
   receiver._environment.restoreSymTab( )

def ppImpl_List_asExpr( anEnv, anArgCt, isLValue=False ):
   receiver = STACK.popAndTestArgs( anArgCt, 'List' )
   theList = receiver._value
   if len(theList) == 0:
      raise PuckException( 'Message list is too short, at least one object excpected.' )

   theReceiver = theList[0]
   theSelector = theList[0] if len(theList) > 1 else None
   theArgs     = [ theReceiver ] + (theList[2:] if len(theList) > 2 else [ ])

   thePkExprInst = makePkExpr( [ theSelector ], theArgs )
   STACK.push( thePkExprInst )

def ppImpl_List_compareTo_( anEnv, anArgCt, isLValue=False ):
   raise PuckException( "List#compareTo: not yet implemented." )

def ppImpl_List_length( anEnv, anArgCt, isLValue=False ):
   receiver = STACK.popAndTestArgs( anArgCt, 'List' )
   STACK.push( PkObject(pkNumberClass, len(receiver._value)) )

def ppImpl_List_at_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'List', 'Number' )

   try:
      STACK.push( receiver._value[arg1._value] )
   except:
      raise PuckException( 'List index out of range.' )

def ppImpl_List_from_to_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1, arg2 = STACK.popAndTestArgs( anArgCt, 'List', 'Number', 'Number' )
   try:
      subList = receiver._value[ arg1._value : arg2._value ]
      theSubPkList = makePkList( subList )
      STACK.push( theSubPkList )
   except:
      raise PuckException( 'List index out of range.' )

def ppImpl_List_add_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'List', 'List' )
   theMergedPkList = makePkList( receiver._value + arg1._value )
   STACK.push( theMergedPkList )

def ppImpl_List_append_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'List', 'Object' )
   receiver._value.append( arg1 )
   STACK.push( receiver )

def ppImpl_List_whileTrue_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgCt, 'List', 'Object' )
   lastResult = None
   STACK.push( receiver )
   STACK_EVAL( "eval", 1, anEnv, False )
   while( STACK.pop() is GLOBAL.get('true') ):
      STACK.push( arg1 )
      STACK_EVAL( 'eval', 1, anEnv, False )
      lastResult = STACK.pop()

      STACK.push( receiver )
      STACK_EVAL( "eval", 1, anEnv, False )

   STACK.push( lastResult )

def ppImpl_List_forEachItem_( anEnv, anArgCt, isLValue=False ):
   receiver, arg1 = STACK.popAndTestArgs( anArgList, 'List', ('List','Primitive') )
   lastResult = None
   for thePkListItem in receiver._value:
      STACK.push( thePkListItem )
      STACK.push( arg1 )
      STACK_EVAL( 'eval', 2, anEnv, False )
      lastResult = STACK.pop()

   STACK.push( lastResult )

# pkExpr Operations
def ppImpl_Expr_eval( anEnv, anArgCt, isLValue=False ):
   receiver = STACK.popAndTestArgs( anArgCt, 'Expression' )
   # In reverse order push each arg and evaluate it.
   numArgs = len(receiver._args)
   for argNum in range(numArgs-1, -1, -1):
      STACK.push( receiver._args[argNum] )
      STACK_EVAL( 'eval', 1, anEnv, (argNum==0) and (receiver._sel=='<-') )

   # Now exec the code indicated by the selector
   STACK_EVAL( receiver._sel, numArgs, anEnv, isLValue )


# ##########################
# Make the Primitive Objects
pkObjectClass    = PkObject( aPkClass=None             )
pkPrimitiveClass = PkObject( aPkClass=pkObjectClass    )
pkNullClass      = PkObject( aPkClass=pkObjectClass    )
pkBooleanClass   = PkObject( aPkClass=pkObjectClass    )
pkMagnitudeClass = PkObject( aPkClass=pkObjectClass    )
pkStringClass    = PkObject( aPkClass=pkMagnitudeClass )
pkNumberClass    = PkObject( aPkClass=pkMagnitudeClass )
pkQuoteClass     = PkObject( aPkClass=pkObjectClass    )
pkSymbolClass    = PkObject( aPkClass=pkObjectClass    )
pkListClass      = PkObject( aPkClass=pkObjectClass    )
pkExprClass      = PkObject( aPkClass=pkObjectClass    )

def makePkNumber( aValue ):
   theNumObj = PkObject( pkNumberClass )
   theNumObj._value = aValue
   return theNumObj

def makePkString( aValue ):
   theStrObj = PkObject( pkStringClass )
   theStrObj._value = aValue
   return theStrObj

def makePkSymbol( aValue ):
   theSymObj = PkObject( pkSymbolClass )
   theSymObj._value = aValue
   return theSymObj

def makePkPrimitive( fn, fnName='' ):
   thePrimitive = PkObject( pkPrimitiveClass, fn, name=PkObject(pkStringClass, fnName) )
   GLOBAL.set( fnName, thePrimitive )

def makePkList( items, anEnv=None, params=None, allLocals=None ):
   anEnv     = anEnv     if anEnv     else PkEnvironment(GLOBAL)
   params    = params    if params    else [ ]
   allLocals = allLocals if allLocals else [ ]
   
   theInst = PkObject( pkListClass, items, parameters=params, allLocals=allLocals )
   theInst._environment = anEnv
   return theInst

def makePkExpr( aKeyList, anArgList ):
   sel = ''.join(aKeyList)
   theInst = PkObject( pkExprClass, ( 'expr', sel, anArgList, aKeyList ) )
   theInst._sel     = sel
   theInst._args    = anArgList
   theInst._keyList = aKeyList
   return theInst

def initializeEnvironment( ):
   pass

makePkPrimitive( ppImpl_Object_sameObjectAs_,            'objectSameObjectAs'            )
makePkPrimitive( ppImpl_Object_isKindOf_,                'objectIsKindOf'                )
makePkPrimitive( ppImpl_Object_equalTo_,                 'objectEquality'                )
makePkPrimitive( ppImpl_Object_notEqualTo_,              'objectInequality'              )
makePkPrimitive( ppImpl_Object_compareTo_,               'objectCompareTo'               )
makePkPrimitive( ppImpl_Object_eval,                     'objectEval'                    )
makePkPrimitive( ppImpl_Object_evalMessage_,             'objectEvalMessage'             )
makePkPrimitive( ppImpl_Object_member_,                  'objectMember'                  )
makePkPrimitive( ppImpl_Object_memberRemove_,            'objectMemberRemove'            )
makePkPrimitive( ppImpl_Object_member_setTo_,            'objectMemberSetTo'             )
makePkPrimitive( ppImpl_Object_selfMember_setTo_,        'objectSelfMemberSetTo'         )
makePkPrimitive( ppImpl_Object_memberList,               'objectMemberList'              )
makePkPrimitive( ppImpl_Object_make,                     'objectMake'                    )
makePkPrimitive( ppImpl_Object_delete,                   'objectDelete'                  )
makePkPrimitive( ppImpl_Object_printValue,               'objectPrintValue'              )
makePkPrimitive( ppImpl_Object_printMembers,             'objectPrintMembers'            )

makePkPrimitive( ppImpl_Primitive_evalForArgs_,          'primitiveEvalForArgs'          )

makePkPrimitive( ppImpl_Boolean_negation,                'booleanNegation'               )
makePkPrimitive( ppImpl_Boolean_and_,                    'booleanAnd'                    )
makePkPrimitive( ppImpl_Boolean_or_,                     'booleanOr'                     )
makePkPrimitive( ppImpl_Boolean_ifTrue_,                 'booleanIfTrue'                 )
makePkPrimitive( ppImpl_Boolean_ifTrue_ifFalse_,         'booleanIfTrueIfFalse'          )

makePkPrimitive( ppImpl_Magnitude_lessThan_,             'magnitudeLessThan'             )
makePkPrimitive( ppImpl_Magnitude_lessThanOrEqualTo_,    'magnitudeLessThanOrEqualTo'    )
makePkPrimitive( ppImpl_Magnitude_greaterThan_,          'magnitudeGreaterThan'          )
makePkPrimitive( ppImpl_Magnitude_greaterThanOrEqualTo_, 'magnitudeGreaterThanOrEqualTo' )

makePkPrimitive( ppImpl_String_compareTo_,               'stringEquality'                )
makePkPrimitive( ppImpl_String_length,                   'stringLength'                  )
makePkPrimitive( ppImpl_String_at_,                      'stringAt'                      )
makePkPrimitive( ppImpl_String_from_to_,                 'stringFromTo'                  )
makePkPrimitive( ppImpl_String_add_,                     'stringAdd'                     )
makePkPrimitive( ppImpl_String_forEachCharacter_,        'stringForEachCharacter'        )
makePkPrimitive( ppImpl_String_parsePuckExpr,            'stringParsePuckExpr'           )

makePkPrimitive( ppImpl_Number_compareTo_,               'numberEquality'                )
makePkPrimitive( ppImpl_Number_add_,                     'numberAdd'                     )
makePkPrimitive( ppImpl_Number_sub_,                     'numberSubtract'                )
makePkPrimitive( ppImpl_Number_mul_,                     'numberMultiply'                )
makePkPrimitive( ppImpl_Number_div_,                     'numberDivide'                  )
makePkPrimitive( ppImpl_Number_pow_,                     'numberPower'                   )
makePkPrimitive( ppImpl_Number_truncate,                 'numberTruncate'                )
makePkPrimitive( ppImpl_Number_doTimes_,                 'numberDoTimes'                 )

makePkPrimitive( ppImpl_Quote_eval,                      'quoteEval'                     )

makePkPrimitive( ppImpl_Symbol_eval,                     'symbolEval'                    )
makePkPrimitive( ppImpl_Symbol_assign_,                  'symbolAssign'                  )

makePkPrimitive( ppImpl_List_eval,                       'listEval'                      )
makePkPrimitive( ppImpl_List_evalForArgs_,               'listEvalForArgs'               )
makePkPrimitive( ppImpl_List_evalInPlace,                'listEvalInPlace'               )
makePkPrimitive( ppImpl_List_asExpr,                     'listAsExpr'                    )
makePkPrimitive( ppImpl_List_compareTo_,                 'listEquality'                  )
makePkPrimitive( ppImpl_List_length,                     'listLength'                    )
makePkPrimitive( ppImpl_List_at_,                        'listAt'                        )
makePkPrimitive( ppImpl_List_from_to_,                   'listFromTo'                    )
makePkPrimitive( ppImpl_List_add_,                       'listAdd'                       )
makePkPrimitive( ppImpl_List_append_,                    'listAppend'                    )
makePkPrimitive( ppImpl_List_whileTrue_,                 'listWhileTrue'                 )
makePkPrimitive( ppImpl_List_forEachItem_,               'listForEachItem'               )

makePkPrimitive( ppImpl_Expr_eval,                       'exprEval'                      )

# ###########################
# Define the Built-In Classes

# Define Class, the base class of all classes
GLOBAL.set( 'Object',     pkObjectClass        )
pkObjectClass._members[ 'name'              ] = PkObject(pkStringClass,'Object')
pkObjectClass._members[ 'sameObjectAs:'     ] = GLOBAL.get( 'objectSameObjectAs'            )
pkObjectClass._members[ 'isKindOf:'         ] = GLOBAL.get( 'objectIsKindOf'                )
pkObjectClass._members[ '='                 ] = GLOBAL.get( 'objectEquality'                )
pkObjectClass._members[ '!='                ] = GLOBAL.get( 'objectInequality'              )
pkObjectClass._members[ 'compareTo:'        ] = GLOBAL.get( 'objectCompareTo'               )
pkObjectClass._members[ 'eval'              ] = GLOBAL.get( 'objectEval'                    )
pkObjectClass._members[ 'evalMessage:'      ] = GLOBAL.get( 'objectEvalMessage'             )
pkObjectClass._members[ 'member:'           ] = GLOBAL.get( 'objectMember'                  )
pkObjectClass._members[ 'member:setTo:'     ] = GLOBAL.get( 'objectMemberSetTo'             )
pkObjectClass._members[ 'selfMember:setTo:' ] = GLOBAL.get( 'objectSelfMemberSetTo'         )
pkObjectClass._members[ 'memberList'        ] = GLOBAL.get( 'objectMemberList'              )
pkObjectClass._members[ 'make'              ] = GLOBAL.get( 'objectMake'                    )
pkObjectClass._members[ 'delete'            ] = GLOBAL.get( 'objectDelete'                  )
pkObjectClass._members[ 'printValue'        ] = GLOBAL.get( 'objectPrintValue'              )
pkObjectClass._members[ 'printMembers'      ] = GLOBAL.get( 'objectPrintMembers'            )

# PkPrimitive Class Definition
GLOBAL.set( 'Primitive',  pkPrimitiveClass     )
pkPrimitiveClass._members[ 'name'           ] = PkObject(pkStringClass,'Primitive')
pkPrimitiveClass._members[ 'evalForArgs:'   ] = GLOBAL.get( 'primitiveEvalForArgs'          )

# PkNull Class Definition
GLOBAL.set( 'Null',       pkNullClass          )
pkNullClass._members[ 'name'                ] = PkObject(pkStringClass,'Null')

# PkBoolean Class Definition
GLOBAL.set( 'Boolean',    pkBooleanClass       )
pkBooleanClass._members[ 'name'             ] = PkObject(pkStringClass,'Boolean')
pkBooleanClass._members[ 'not'              ] = GLOBAL.get( 'booleanNegation'               )
pkBooleanClass._members[ 'and'              ] = GLOBAL.get( 'booleanAnd'                    )
pkBooleanClass._members[ 'or'               ] = GLOBAL.get( 'booleanOr'                     )
pkBooleanClass._members[ 'ifTrue:'          ] = GLOBAL.get( 'booleanIfTrue'                 )
pkBooleanClass._members[ 'ifTrue:ifFalse:'  ] = GLOBAL.get( 'booleanIfTrueIfFalse'          )

# PkMagnitude Class Definition
GLOBAL.set( 'Magnitude',  pkMagnitudeClass     )
pkMagnitudeClass._members[ 'name'           ] = PkObject(pkStringClass,'Magnitude')
pkMagnitudeClass._members[ '<'              ] = GLOBAL.get( 'magnitudeLessThan'             )
pkMagnitudeClass._members[ '>'              ] = GLOBAL.get( 'magnitudeGreaterThan'          )
pkMagnitudeClass._members[ '<='             ] = GLOBAL.get( 'magnitudeLessThanOrEqualTo'    )
pkMagnitudeClass._members[ '>='             ] = GLOBAL.get( 'magnitudeGreaterThanOrEqualTo' )

# PkString Class Definition
GLOBAL.set( 'String',     pkStringClass        )
pkStringClass._members[ 'name'              ] = PkObject(pkStringClass,'String')
pkStringClass._members[ 'compareTo:'        ] = GLOBAL.get( 'stringEquality'                )
pkStringClass._members[ 'length'            ] = GLOBAL.get( 'stringLength'                  )
pkStringClass._members[ 'at:'               ] = GLOBAL.get( 'stringAt'                      )
pkStringClass._members[ 'from:to:'          ] = GLOBAL.get( 'stringFromTo'                  )
pkStringClass._members[ '+'                 ] = GLOBAL.get( 'stringAdd'                     )
pkStringClass._members[ 'forEachCharacter:' ] = GLOBAL.get( 'stringForEachCharacter'        )
pkStringClass._members[ 'parsePuckExpr'     ] = GLOBAL.get( 'stringParsePuckExpr'           )

# PkNumber Class Defintion
GLOBAL.set( 'Number',     pkNumberClass        )
pkNumberClass._members[ 'name'              ] = PkObject(pkStringClass,'Number')
pkNumberClass._members[ 'compareTo:'        ] = GLOBAL.get( 'numberEquality'                )
pkNumberClass._members[ '+'                 ] = GLOBAL.get( 'numberAdd'                     )
pkNumberClass._members[ '-'                 ] = GLOBAL.get( 'numberSubtract'                )
pkNumberClass._members[ '*'                 ] = GLOBAL.get( 'numberMultiply'                )
pkNumberClass._members[ '/'                 ] = GLOBAL.get( 'numberDivide'                  )
pkNumberClass._members[ '^'                 ] = GLOBAL.get( 'numberPower'                   )
pkNumberClass._members[ 'truncate'          ] = GLOBAL.get( 'numberTruncate'                )
pkNumberClass._members[ 'doTimes:'          ] = GLOBAL.get( 'numberDoTimes'                 )

# PkQuote Class Definition
GLOBAL.set( 'Quote',      pkQuoteClass         )
pkQuoteClass._members[ 'name'               ] = PkObject(pkStringClass,'Quote')
pkQuoteClass._members[ 'eval'               ] = GLOBAL.get( 'quoteEval'                     )

# PkSymbol Class Definition
GLOBAL.set( 'Symbol',     pkSymbolClass        )
pkSymbolClass._members[ 'name'              ] = PkObject(pkStringClass,'Symbol')
pkSymbolClass._members[ 'eval'              ] = GLOBAL.get( 'symbolEval'                    )
pkSymbolClass._members[ '<-'                ] = GLOBAL.get( 'symbolAssign'                  )

# PkList Class Definition
GLOBAL.set( 'List',       pkListClass          )
pkListClass._members[ 'name'                ] = PkObject(pkStringClass,'List')
pkListClass._members[ 'eval'                ] = GLOBAL.get( 'listEval'                      )
pkListClass._members[ 'evalForArgs:'        ] = GLOBAL.get( 'listEvalForArgs'               )
pkListClass._members[ 'evalInPlace'         ] = GLOBAL.get( 'listEvalInPlace'               )
pkListClass._members[ 'asExpr'              ] = GLOBAL.get( 'listAsExpr'                    )
pkListClass._members[ 'compareTo:'          ] = GLOBAL.get( 'listEquality'                  )
pkListClass._members[ 'length'              ] = GLOBAL.get( 'listLength'                    )
pkListClass._members[ 'at:'                 ] = GLOBAL.get( 'listAt'                        )
pkListClass._members[ 'from:to:'            ] = GLOBAL.get( 'listFromTo'                    )
pkListClass._members[ '+'                   ] = GLOBAL.get( 'listAdd'                       )
pkListClass._members[ 'append:'             ] = GLOBAL.get( 'listAppend'                    )
pkListClass._members[ 'whileTrue:'          ] = GLOBAL.get( 'listWhileTrue'                 )
pkListClass._members[ 'forEachItem:'        ] = GLOBAL.get( 'listForEachItem'               )

# PkExpr Class Definition
GLOBAL.set( 'Expression', pkExprClass          )
pkExprClass._members[ 'name'                ] = PkObject(pkStringClass,'Expr')
pkExprClass._members[ 'eval'                ] = GLOBAL.get( 'exprEval'                      )

# Add the predefined instances
GLOBAL.set( 'null',       PkObject(pkNullClass,    'null') )
GLOBAL.set( 'true',       PkObject(pkBooleanClass, True  ) )
GLOBAL.set( 'false',      PkObject(pkBooleanClass, False ) )

