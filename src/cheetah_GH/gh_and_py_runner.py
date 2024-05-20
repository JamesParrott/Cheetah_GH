#! /python3
# -*- coding: utf-8 -*-
# This test launcher script requires Python 3.8 or higher (for f'{x=}') and an installation of Rhino 8.



import os
import sys
import pathlib
import socketserver
import multiprocessing
import subprocess




# https://docs.python.org/3/library/socketserver.html#socketserver-udpserver-example 
class MyUDPHandler(socketserver.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """

    quit_on = 'TESTS_FAILED'

    def handle(self):
        data = self.request[0].strip()
        socket = self.request[1]
        output = data.decode('utf-8')
        print(output)
        if output == self.quit_on:
            sys.exit(1)
        # self.__class__.last_output.append(output)
        # socket.sendto(data.upper(), self.client_address)

def start_UDP_server():
    HOST, PORT = "127.0.0.1", 9999
    with socketserver.UDPServer((HOST, PORT), MyUDPHandler) as server:
        server.serve_forever()


if __name__ == '__main__':
    p = multiprocessing.Process(target=start_UDP_server)
    p.daemon = True
    print('Starting output printing UDP server.  Press Ctrl+C to quit.')
    p.start()

    # Test output over UDP to stdout from RhinoPython
    # client_path = pathlib.Path(__file__).parent / 'client.py'
    # subprocess.run(rf'"C:\Program Files\Rhino 8\System\Rhino.exe" /nosplash /runscript="_-RunPythonScript {client_path} _enter _exit _enterend"')

    # test_gh_file_path = pathlib.Path(__file__).parent / 'Rhino_8_Read_Geom_(Rhino)_and_Recolour_Objects_test.gh'
    test_gh_file_path = pathlib.Path(__file__).parent / "Rhino_8_API_tests.gh"

    # TODO:    Refactor all this block as:
    # cheetah.run(test_gh_file_path, env = env, quit_on = 'TESTS_FAILED', protocol='UDP', host = '127.0.0.1', port=9999)

    print(rf'Opening: {test_gh_file_path}')
    env = os.environ.copy()
    
    # Exit Rhino afterwards.
    env['CHEETAH_GH_NON_INTERACTIVE'] = 'True'
    
    # Number of Fuzz tests to run.
    env['NUM_TESTS'] = sys.arg[1] if len(sys.argv) >= 2 else '5'
    
    #if test_gh_file_path.endswith('.gh'):

    result = subprocess.run(rf'"C:\Program Files\Rhino 8\System\Rhino.exe" /nosplash /runscript="-_grasshopper _editor _load _document _open {test_gh_file_path}  _enter _exit _enterend"'
                           ,env = env
                           )
    # else:  # assert test_gh_file_path.endswith('.py') # => run with Rhinoscript. 
    p.terminate()

    print(f'{result.returncode=}')
    print(f'{p.exitcode=}')

    # print(MyUDPHandler.last_output)
    # print('TESTS_FAILED' in ''.join(MyUDPHandler.last_output)[-100:])

    if result.returncode != 0 or p.exitcode: #'TESTS_FAILED' in ''.join(MyUDPHandler.last_output):
        raise Exception('Some tests were failed (or an error occurred during testing). \n'
                        f'Test runner retcode: {result.returncode}\n'
                        f'Test output server exitcode: {p.exitcode}\n'
                        )


    sys.exit(0)