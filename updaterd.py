import configparser
import argparse
import os

import pygit2


parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-c', '--config', type=str, default='config.ini',
                    help='Config file to use')
parser.add_argument('-f', '--force', dest='force', action='store_true',
                    help='sum the integers (default: find the max)')


class UpdateRepo(object):

    def __init__(self, path, config):
        super().__init__()

        self.path = os.path.join(path, '.git')
        self.config = config

        # Connect to or clone repo
        if os.path.exists(self.path):
            self.repo = pygit2.Repository(self.path)
        else:
            print('Cloning %s from %s' % (path, config['url']))
            self.repo = pygit2.clone_repository(config['url'], self.path)


if __name__ == '__main__':

    repos = {}

    args = parser.parse_args()
    print(args)

    config = configparser.ConfigParser()
    config.read(args.config)
    for sec in [x for x in config.sections() if x != '.']:
        repos[sec] = UpdateRepo(sec, config[sec])
