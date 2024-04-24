import click
import numpy as np
from ruamel.yaml import YAML

@click.command()
@click.option('--world',  default = '../../../ADF/world/world_stereo.yaml', help='path to ADF file "world.yaml".')
@click.option('--camera',  default = 'main_camera', help='name of camera defined in "world.yaml".')
@click.option('--intrin', help='path to camera intrinsic matrix in .npy or .yaml format.')
def main(world, camera, intrin):

    # Load world ADF file
    yaml = YAML()
    yaml.boolean_representation = [u'false', u'true']

    with open(world, 'r') as f:
            params = yaml.load(f)
            f.close()
    camera_param = params[camera]

    near = camera_param['clipping plane']['near']
    far = camera_param['clipping plane']['far']
    width = camera_param['publish image resolution']['width']
    height = camera_param['publish image resolution']['height']


    K = np.zeros([3,3])
    # camera intrinsic matrix
    if (intrin.endswith('.npy')):
        K = np.load(intrin)
    elif(intrin.endswith('.yaml')):
        with open(intrin, 'r') as f:
            params = yaml.load(f)
            f.close()
        frame_height = params['frame_height']
        frame_width  = params['frame_width']
        fx = params['fx']
        fy = params['fy']
        ppx = params['ppx']
        ppy = params['ppy']

        print(frame_height)
        print(frame_width)
        print(fx)
        print(fy)
        print(ppx)
        print(ppy)

        K[0,0] = fx#/frame_width
        K[1,1] = fy#/frame_height
        K[0,2] = ppx#/frame_width
        K[1,2] = ppy#/frame_height
        
    print('Camera Intrinsic Matrix:', K)

    depth = far - near
    p_M = np.zeros([4,4])

    # From Hong Chao's code
    p_M[0, 0] = 2*K[0,0]/width
    p_M[0, 2] = (width - 2*K[0,2])/width
    p_M[1, 1] = 2*K[1,1]/height
    p_M[1, 2] = (-height + 2*K[1,2])/height
    p_M[2, 2] = (-far - near)/depth
    p_M[2, 3] = -2*(far*near)/depth
    p_M[3, 2] = -1

    # From Hisashi
    # https://www.songho.ca/opengl/gl_projectionmatrix.html
    p_M[0, 0] = 2*K[0,0]/width
    p_M[0, 2] = (2*K[0,2])/width
    p_M[1, 1] = 2*K[1,1]/height
    p_M[1, 2] = (2*K[1,2])/height
    p_M[2, 2] = (-far - near)/depth
    p_M[2, 3] = -2*(far*near)/depth
    p_M[3, 2] = -1
    print(repr(p_M))


if __name__ == '__main__':
    main()
    