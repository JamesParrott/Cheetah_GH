
# https://discuss.python.org/t/custom-build-steps-moving-bokeh-off-setup-py/16128/3
from hatchling.builders.hooks.plugin.interface import BuildHookInterface

class CustomHook(BuildHookInterface):
    def initialize(self, version, build_data):
        if True: #self.target_name in ('wheel', 'bdist'):
            with open('dookie.txt','wt') as f:
                f.write('Badork!\n\n')
    
    # def build_ext(self):
        
    #     raise Exception('Nope!!')
    #     if True: #self.target_name in ('wheel', 'bdist'):
    #         with open('dookie.txt','wt') as f:
    #             f.write('Badork!\n\n')