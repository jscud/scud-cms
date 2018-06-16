import os
import sys

APP_YAML_PREAMBLE = '''runtime: python27
api_version: 1
threadsafe: true

handlers:
- url: /
  static_files: index.html
  upload: index\.html
'''


def write_app_yaml(files, directories):
  new_app_yaml = open('%s/app.yaml' % sys.argv[1], 'w')
  new_app_yaml.write(APP_YAML_PREAMBLE)
  new_app_yaml.close()


def main():
    if len(sys.argv) < 2:
        print('Provide a directory which contains the website files.')
        print('For example, run %s example_site' % sys.argv[0])
        return 1

    found_index_html = False
    files = []
    directories = []
    filenames = os.listdir(sys.argv[1])
    for filename in filenames:
        print('Filename: %s' % filename)
        if filename == 'index.html':
            found_index_html = True
        elif os.path.isdir(filename):
            directories.append(filename)
        elif filename != 'app.yaml':
            files.append(filename)

    if found_index_html:
        write_app_yaml(files, directories)
    else:
        print('The directory %s must contain an index.html file.' % (
            sys.argv[1],))
        return 1


if __name__ == '__main__':
    main()
