from PuckParser import PuckParser, ParseError
import Object
import traceback

class Listener( object ):
   def __init__( self ):
      super().__init__( )

      self._listenerCommandSet = {
         'log <filename>':      ( 'Begin logging.',                    self.execLogListenerCommand   ),
         'read <filename>':     ( 'Read and execute a log file.',      self.execReadListenerCommand  ),
         'continue <filename>': ( 'Continue a prior logging seesion.', self.execContinueListenerCommand ),
         'close':               ( 'Stop logging.',                     self.execCloseListenerCommand ),
         'reset':               ( 'Reset the Puck environment.',       self.execResetListenerCommand ),
         'exit':                ( 'Exit Puck listener.',               self.execExitListenerCommand  ),
         'help':                ( 'Display this help.',                self.execHelpListenerCommand  )
         }

      self._logFile = None

   def execLogListenerCommand( self, cmdParts ):
      if len(cmdParts) != 2:
         print( 'Use:  log <filename>, to begin a new logging session.' )
         return

      cmd, filename = cmdParts
      if self._logFile is not None:
         self._logFile.close( )

      self._logFile = open( filename, 'w' )

   def execReadListenerCommand( self, cmdParts ):
      print( 'Not yet implemented.' )

   def execContinueListenerCommand( self, cmdParts ):
      print( 'Not yet implemented.' )

   def execCloseListenerCommand( self, cmdParts ):
      if self._logFile is not None:
         self._logFile.close( )

   def execResetListenerCommand( self, cmdParts ):
      Object.initializeEnvironment( )

   def execExitListenerCommand( self, cmdParts ):
      raise PuckParser( )

   def execHelpListenerCommand( self, cmdParts ):
      for cmd, parts in self._listenerCommandSet.items():
         print( '{0:<10} {1}'.format( cmd, parts[0] ) )

   def execListenerCommand( self, listenerCommand ):
      cmdParts = listenerCommand[1:].split( ' ' )
      cmdParts = [ x for x in cmdParts if x != '' ]
      try:
         commandHandler = self._listenerCommandSet[ cmdParts[0] ][ 1 ]
      except:
         print( 'Unknown listener command.' )
         return

      commandHandler( cmdParts )

   def readEvalPrintLoop( self ):
      parser = PuckParser( Object.GLOBAL )
      expressionStr = ''

      while True:
         if expressionStr == '':
            lineInput = input( '>>> ' )
         else:
            lineInput = input( '... ' )

         if (lineInput.strip() == '') and (expressionStr.strip() != ''):
            if expressionStr[0] == ']':
               self.execListenerCommand( expressionStr )
            else:
               try:
                  expr = parser.parse( expressionStr )
                  #print( Object.printable(expr) )
                  result = Object.EVAL_OBJ_R( expr )
                  resultStr = Object.printable(result)
                  print( resultStr )

               except ParseError as ex:
                  print( ex.generateVerboseErrorString() )

               except Object.PuckException as ex:
                  print( ex )
                  traceback.print_exc( )

               except Exception as ex:
                  print( ex )
                  traceback.print_exc( )

               print( )
            expressionStr = ''
         else:
            expressionStr += (lineInput.strip() + '\n')

if __name__ == '__main__':
   listener = Listener( )
   listener.readEvalPrintLoop( )
