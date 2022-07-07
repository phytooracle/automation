import yaml

def preprocess_yaml_file(yaml_path, date, args):

    substitutions = {
            '{{$DATE}}' : date
    }

    yaml_lines = []
    with open(args.yaml, "r") as f_in:
        for line in f_in:
            for key, value in substitutions.items():
                new_line = line.replace(key, value)
            yaml_lines.append(new_line)
    return yaml.safe_load("\n".join(yaml_lines))

                       
class YamlFilePreprocessor(object):

    def __init__(self, season=None, sensor=None, date=None):
        return 

class YamlDictPreprocessor(object):

    def __init__(self, season=None, sensor=None, date=None):
        pass
