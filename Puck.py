import ltk_py3.Listener as Listener
from ltk_py3.Listener import EvaluationError
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
      expr = self._parser.parse( anExprStr )   # May raise ParseError
      try:
         result = PuckImpl.evalPuckExpr( expr, stdin=stdin, stdout=stdout, stderr=stderr )
      except Exception as ex:
         raise EvaluationError from ex
   
      return PuckImpl.printable(result)
   
   def safe_eval( self, anExprStr, stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr ):
      '''safe_eval is guarantees the caller will not see an exception.  Instead
      all exceptions are diverted to the sys.stdout stream.
      '''
      try:
         expr = self._parser.parse( anExprStr )   # May raise ParseError
         return self._interp.eval( inputText, stdout=con_out, stderr=ev_err )
      
      except Scanner.ParseError as ex:
         self._exceptInfo = sys.exc_info( )
         print( ex.generateVerboseErrorString(), file=stderr )

      except EvaluationError as ex:
         self._exceptInfo = sys.exc_info( )
         print( ex.args[-1], file=con_err )

      except Exception as ex:
         self._exceptInfo = sys.exc_info( )
         print( ex.args[-1] )
         raise                                      # Should NEVER OCCUR

   def runtimeLibraries( self ):
      return [ ]
   
   def testFileList( self ):
      return [ ]
   
if __name__ == '__main__':
   puckInterp = PuckInterpreter( )
   listener = Listener.Listener( puckInterp, language='Puck', version='0.1' )
   listener.readEvalPrintLoop( )
