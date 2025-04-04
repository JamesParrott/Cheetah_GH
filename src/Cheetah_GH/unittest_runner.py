import os
import sys
import unittest
import time
import io

from .helpers import FileAndStream, UDPStream, exit_Rhino



def run_unittest(output_stream = sys.stderr
                ,log_file = ''
                ,test_suite = ()
                ,start_dir = ''
                ):
    #type: [io.TextIOBase, str, unittest.TestSuite | (), str] -> unittest.TextTestResult


    if os.getenv('CHEETAH_GH_NON_INTERACTIVE', '').lower() in ('', '0', 'false'):
        exit = False 
    else:
        exit = True


    output_stream.write(
        'Exit Rhino after tests: %s (env var CHEETAH_GH_NON_INTERACTIVE)'
        % ('Yes' if exit else 'No')
        )

    if not test_suite:

        output_stream.write('Loading unit tests from: %s \n' % start_dir)
        test_suite = unittest.TestLoader().discover(start_dir = start_dir
                                                    # Non standard pattern ensures 
                                                    # tests requiring Grasshopper are
                                                    # skipped by the default discovery 
                                                    ,pattern = '*test*.py'
                                                    )
    else:
        output_stream.write('Using test_suite: %s' % test_suite)



    if log_file:
        
        file_ = open(log_file,'at')
        output_stream = FileAndStream(
                                 file_
                                ,output_stream
                                ,print_too = output_stream is not sys.stderr
                                )


    with output_stream as o:

        o.write('Unit test run started at: %s ... \n\n' % time.asctime())

        result = unittest.TextTestRunner(o, verbosity=2).run(test_suite)
        
        o.write('Test Summary\n')
        o.write('Errors: %s\n' % (result.errors,))
        o.write('Failures: %s\n' % (result.failures,))

        if not result.wasSuccessful():
            # Special string to tell run_api_tests to return non-zero exit code
            o.write('TESTS_FAILED')


    if exit and result.wasSuccessful():
        exit_Rhino()


    return result


def start(log_file = ''
         ,test_suite = ()
         ,start_dir = ''
         ,port=9999
         ,host='127.0.0.1'
         ):
    #type: [str, unittest.TestSuite | (), str, int, str] -> unittest.TextTestResult
    return run_unittest(output_stream = UDPStream(port, host)
                       ,log_file = log_file
                       ,test_suite = test_suite
                       ,start_dir = start_dir
                       )