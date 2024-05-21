#! /python3
# -*- coding: utf-8 -*-
# This test launcher script requires Python >=3.8 and an installation of Rhino 8.



import os
import sys
import socketserver
import multiprocessing
import subprocess




class MyUDPHandler(socketserver.BaseRequestHandler):

    quit_on = 'TESTS_FAILED'

    def handle(self):
        data = self.request[0].strip()

        output = data.decode('utf-8')
        print(output)
        if output == self.quit_on:
            sys.exit(1)


def start_UDP_server():
    HOST, PORT = "127.0.0.1", 9999
    with socketserver.UDPServer((HOST, PORT), MyUDPHandler) as server:
        server.serve_forever()


if __name__ == '__main__':
    p = multiprocessing.Process(target=start_UDP_server)
    p.daemon = True
    print('Starting output printing UDP server.  Press Ctrl+C to quit.')
    p.start()


    gh_file_path = sys.argv[1]

    env = os.environ.copy()

    # By default, exit Rhino afterwards.
    env['CHEETAH_GH_NON_INTERACTIVE'] = 'True'


    # Subsequent trailing command line args are env variable names and values.
    other_args = iter(sys.argv[2:])
    env.update(zip(other_args, other_args))

    
    

    print(rf'Opening: {gh_file_path}')

    result = subprocess.run(
         ( r'"C:\Program Files\Rhino 8\System\Rhino.exe" /nosplash /runscript='
          rf'"-_grasshopper _editor _load _document _open {gh_file_path} '
           r'_enter _exit _enterend"'
         )
        ,env = env
        )
    p.terminate()

    print(f'{result.returncode=}')
    print(f'{p.exitcode=}')


    if result.returncode != 0 or p.exitcode: 
        raise Exception(
             'Some tests were failed (or an error occurred during testing). \n'
            f'Test runner retcode: {result.returncode}\n'
            f'Test output server exitcode: {p.exitcode}\n'
            )


    sys.exit(0)