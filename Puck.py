import ltk_py3.Listener as Listener
from PuckParser import PuckParser
import PuckImpl
import traceback
import sys

class PuckInterpreter( Listener.Interpreter ):
   def __init__( self ):
      super().__init__()
      self._parser = PuckParser( PuckImpl.GLOBAL )
   
   def reboot( self ):
      pass
   
   def eval( self, anExprStr, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr ):
      expr = self._parser.parse( anExprStr )
      result = PuckImpl.EVAL_OBJ_R( expr )
      return PuckImpl.printable(result)

   def runtimeLibraries( self ):
      return [ ]
   
   def testFileList( self ):
      return [ ]
   
if __name__ == '__main__':
   puckInterp = PuckInterpreter( )
   listener = Listener.Listener( puckInterp, language='Puck', version='0.1' )
   listener.readEvalPrintLoop( )
