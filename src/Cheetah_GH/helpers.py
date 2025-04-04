#! /usr/bin/awk NR==3
# -*- coding: utf-8 -*-
# This module requires Grasshopper Python (Rhino3D)



import os 
from collections import OrderedDict
import ctypes
import socket
import tempfile

import System

import Rhino
try:
    import Rhino.NodeInCode.Components
except ImportError:
    import Rhino.NodeInCode
import Grasshopper
import rhinoscriptsyntax as rs


TMP = tempfile.gettempdir()

DIR = os.path.join(TMP, 'Cheetah_GH')

if not os.path.isdir(DIR):
    os.makedirs(DIR) 

try:
    ghdoc
except NameError:
    import scriptcontext as sc

    if sc.doc == Rhino.RhinoDoc.ActiveDoc:
        raise Exception('Set sc.doc = ghdoc and run the component again.')

    ghdoc = sc.doc

GH_DOC = ghdoc.Component.Attributes.DocObject.OnPingDocument()


def GH_doc_components(doc = GH_DOC):
    return {component.NickName : component
            for component in doc.Objects
           }

GH_DOC_COMPONENTS = GH_doc_components()

GH_TYPE_CONVERTERS = {str : [Grasshopper.Kernel.Types.GH_String]
                     ,bool : [Grasshopper.Kernel.Types.GH_Boolean]
                     ,int : [Grasshopper.Kernel.Types.GH_Integer]
                     ,float : [Grasshopper.Kernel.Types.GH_Number]
                     }

def convert_GH_type_to_Python_type(x):
    for PythonType, v in GH_TYPE_CONVERTERS.items():
        for GH_Type in v:
            if isinstance(x, GH_Type):
                return PythonType(str(x))

    return x


def DataTree_to_GH_Struct(data_tree, type_ = str):
    # https://mcneel.github.io/grasshopper-api-docs/api/grasshopper/html/T_Grasshopper_Kernel_Data_GH_Structure_1.htm
    #
    # https://mcneel.github.io/grasshopper-api-docs/api/grasshopper/html/T_Grasshopper_DataTree_1.htm
    #
    Type_ = GH_TYPE_CONVERTERS[type_][0]
    gh_struct = Grasshopper.Kernel.Data.GH_Structure[Type_]()

    for path in data_tree.Paths:
        for item in data_tree.Branch(path):
            gh_str = Type_(type_(item))
            gh_struct.Append(gh_str, path)

    return gh_struct

def GH_Struct_to_DataTree(gh_struct):
    # https://mcneel.github.io/grasshopper-api-docs/api/grasshopper/html/T_Grasshopper_Kernel_Data_GH_Structure_1.htm
    #
    # https://mcneel.github.io/grasshopper-api-docs/api/grasshopper/html/T_Grasshopper_DataTree_1.htm
    #
    data_tree = Grasshopper.DataTree[object]()
    for path in gh_struct.Paths:
        branch = gh_struct.Branch[path]
        for item in branch:
            data_tree.Add(item, path)

    return data_tree


def set_data_on(param, val, type_ = str):
    param.ClearData()    
    # "and isinstance(val, Grasshopper.DataTree[object])""
    # mimicks Grasshopper support for passing a list into a Tree access param
    if (param.Access == Grasshopper.Kernel.GH_ParamAccess.tree
        and isinstance(val, Grasshopper.DataTree[object])):
        #
        gh_struct = DataTree_to_GH_Struct(val, type_)
        param.AddVolatileDataTree(gh_struct)
    elif isinstance(val, (list, tuple)):
        for i, item in enumerate(val):
            param.AddVolatileData(Grasshopper.Kernel.Data.GH_Path(0), i, item)
    else: 
        param.AddVolatileData(Grasshopper.Kernel.Data.GH_Path(0), 0, val)


def get_data_from(param):


    if param.Access == Grasshopper.Kernel.GH_ParamAccess.tree:
        # return param.VolatileData

        return GH_Struct_to_DataTree(param.VolatileData)

    
    data_tree = Grasshopper.DataTree[object](param.VolatileData)
    
    if data_tree.DataCount >= 1: # Alternative: param.VolatileDataCount >= 1 
        return [convert_GH_type_to_Python_type(x) for x in data_tree.AllData()]
    else:
        branch = data_tree.Branch(0)
        return branch[0] if branch else None

    

    raise NotImplementedError('Unsupported Param.Access value %s. '
                             +'Supported: item, list and tree. '
                             % param.Access
                             )
    


def all_docs_comps():
   return {os.path.splitext(os.path.basename(doc.FilePath))[0] : (doc, GH_doc_components(doc)) 
           for doc in Grasshopper.Instances.DocumentServer.GetEnumerator() 
          }



def get_plugin_files(plugin_name = ''):

    gh_comp_server = Grasshopper.Kernel.GH_ComponentServer()
    #print(list(gh_comp_server.FindObjects(guid)))

    return OrderedDict((os.path.splitext(file_.FileName)[0], file_)
                        for file_ in gh_comp_server.ExternalFiles(True, True)
                        if plugin_name.lower() in file_.FilePath.lower()
                       )


def get_position(comp_number, row_width = 800, row_height = 175, pos = (200, 550)):
    h = comp_number * row_height
    x = pos[0] + (h % row_width)
    y = pos[1] + 220 * (h // row_width)
    return x, y

def add_instance_of_userobject_to_canvas(
    name,
    plugin_files = None,
    plugin_name = '',
    comp_number=1,
    pos = (200, 550),
    ):
    
    plugin_files = plugin_files or get_plugin_files(plugin_name)
    
    file_obj = next((v
                     for k, v in plugin_files.items() 
                     if name.lower() in k.lower()
                    )
                    ,None)
                    
    if file_obj is None:
        raise Exception('No user object found called: %s' % name)
    

                    
    user_obj = Grasshopper.Kernel.GH_UserObject(file_obj.FilePath)

    comp_obj = user_obj.InstantiateObject()
    
    comp_obj.Locked = False
    
    
    
    sizeF = System.Drawing.SizeF(*get_position(comp_number, pos=pos))
    
    
    comp_obj.Attributes.Pivot = System.Drawing.PointF.Add(
                                            comp_obj.Attributes.Pivot,
                                            sizeF
                                            )
    
    success = GH_DOC.AddObject(docObject = comp_obj, update = False)
    
    if not success:
        raise Exception('Could not add comp: %s to GH canvas' % comp_obj)
    
    return comp_obj 



def run_comp(comp, **kwargs):
    
    comp.ClearData()
    #    comp.ExpireSolution(False)
    for param in comp.Params.Input:
        if param.NickName in kwargs:
            set_data_on(param, kwargs[param.NickName])
    comp.CollectData()
    comp.ComputeData()

    return {param.NickName : get_data_from(param) 
            for param in comp.Params.Output
           }


def get_user_obj_comp_from_or_add_to_canvas(
    name,
    plugin_files = None,
    plugin_name = '',
    ):
    
    if name not in GH_DOC_COMPONENTS:
        comp = add_instance_of_userobject_to_canvas(
                            name,
                            plugin_files,
                            plugin_name
                            )
        GH_DOC_COMPONENTS[name] = comp

    return GH_DOC_COMPONENTS[name]


class FileAndStream(object):
    def __init__(self, file, stream, print_too = False):
        self.file = file
        self.stream = stream
        if hasattr(file, 'fileno'):
            self.fileno = file.fileno
        self.print_too = print_too
        
    def write(self, *args):
        self.stream.write(*args)
        self.file.write(*args)
        if self.print_too:
            print(', '.join(args))
        
    def flush(self, *args):
        self.stream.flush()
        self.file.flush()
        
    def __enter__(self):
        self.file.__enter__()
        return self
        
    def __exit__(self, *args):
        return self.file.__exit__(*args)    


class UDPStream(object):
    def __init__(self, port, host):
        self.port = port
        self.host = host
        # SOCK_DGRAM is the socket type to use for UDP sockets
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    def write(self, str_):
        # https://docs.python.org/3/library/socketserver.html#socketserver-udpserver-example
        data = str_.encode("utf-8")
        self.sock.sendto(data, (self.host, self.port))

    def flush(self):
        pass





def save_doc_to_(name, dir_ = None):
    # 'Dale Fugier'
    # https://discourse.mcneel.com/t/sys-exit-shows-popup-window-instead-of-just-exiting/163811/7

    dir_ = dir_ or DIR

    path = os.path.join(dir_, name) if dir_ else name
    rs.Command('_-SaveAs ' + path, True)
    





def exit_Rhino(save_3dm_to = None, save_to_dir = None):
    #'Dale Fugier'
    # https://discourse.mcneel.com/t/sys-exit-shows-popup-window-instead-of-just-exiting/163811/7

    if save_3dm_to:
        save_doc_to_(name = save_3dm_to, dir_ = save_to_dir)

    Rhino.RhinoDoc.ActiveDoc.Modified = False

    hWnd = Rhino.RhinoApp.MainWindowHandle()

    # TODO:  Fix.  Doesn't skip save file screen anymore.
    ctypes.windll.user32.PostMessageW(hWnd, 0x0010, 0, 0) # - quits but doesn't set return code
    # ctypes.windll.user32.PostQuitMessage(ret_code) # - doesn't quit, even if Rhino doc saved.
    # ctypes.windll.user32.PostMessageW(hWnd, 0x0010, ret_code, 0) # - quits but doesn't set return code
    # ctypes.windll.user32.PostMessageW(hWnd, 0x0012, ret_code, 0) # - makes Rhino hang. ret code 1 is set
    #                                                              # after killing it from Task Manager.






def make_callable_using_node_in_code(name):
    func_info = Rhino.NodeInCode.Components.FindComponent(name)
    
    #    if (func_info == null) { Print("Error finding function"); return; }
    
    func = func_info.Delegate #as dynamic;

    return func


    