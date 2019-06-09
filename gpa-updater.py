#!/usr/bin/env python3
import configparser
import argparse
import os

import pygit2


parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-c', '--config', type=str, default='config.ini',
                    help='Config file to use')
parser.add_argument('-f', '--force', dest='force', action='store_true',
                    help='Force update')
parser.add_argument('-d', '--directory', type=str, default=os.getcwd(),
                    help='Root directory, defaults to cwd')


class UpdateRepo(object):

    def __init__(self, path, config):
        super().__init__()

        self.path = os.path.join(path, '.git')
        self.config = config

        # Connect to or clone repo
        if os.path.exists(self.path):
            print('- Found repo at \'%s\'' % path)
            self.repo = pygit2.Repository(self.path)
        else:
            print('- Cloning repo \'%s\' from \'%s\'' % (path, config['url']))
            self.repo = pygit2.clone_repository(config['url'], self.path,
                                                checkout_branch=config.get('branch', fallback='master'))

    def pull(self, remote_name='origin', branch='master'):
        for remote in self.repo.remotes:
            if remote.name == remote_name:
                remote.fetch()
                remote_master_id = self.repo.lookup_reference('refs/remotes/%s/%s' % (remote_name, branch)).target
                merge_result, _ = self.repo.merge_analysis(remote_master_id)
                # Up to date, do nothing
                if merge_result & pygit2.GIT_MERGE_ANALYSIS_UP_TO_DATE:
                    print("Already up to date")
                    return
                # We can just fastforward
                elif merge_result & pygit2.GIT_MERGE_ANALYSIS_FASTFORWARD:
                    print("Fast-forwarding...")
                    self.repo.checkout_tree(self.repo.get(remote_master_id))
                    try:
                        master_ref = self.repo.lookup_reference('refs/heads/%s' % (branch))
                        master_ref.set_target(remote_master_id)
                    except KeyError:
                        self.repo.create_branch(branch, self.repo.get(remote_master_id))
                    self.repo.head.set_target(remote_master_id)
                elif merge_result & pygit2.GIT_MERGE_ANALYSIS_NORMAL:
                    print("Merging...")
                    self.repo.merge(remote_master_id)

                    if self.repo.index.conflicts is not None:
                        for conflict in self.repo.index.conflicts:
                            print('Conflicts found in:', conflict[0].path)

                        raise AssertionError('Conflicts, ahhhhh!!')

                    user = self.repo.default_signature
                    tree = self.repo.index.write_tree()
                    commit = self.repo.create_commit('HEAD', user,  user, 'Merge!', tree,
                                                     [self.repo.head.target, remote_master_id])
                    # We need to do this or git CLI will think we are still merging.
                    self.repo.state_cleanup()
                else:

                    raise AssertionError('Unknown merge analysis result')

    def update(self, force=False):
        _force = force or self.config.getboolean('force', fallback=False)

        self.pull(remote_name=self.config.get('remote', fallback='origin'),
                  branch=self.config.get('branch', fallback='master'))

    def __str__(self) -> str:
        return '%s' % self.path


if __name__ == '__main__':

    repos = {}
    args = parser.parse_args()

    # Read config file
    config = configparser.ConfigParser()
    config.read(args.config)

    #
    for sec in [x for x in config.sections() if x != '.']:
        path = os.path.join(args.directory, sec)

        repos[path] = UpdateRepo(path, config[sec])
        repos[path].update()
