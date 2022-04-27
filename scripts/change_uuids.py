import os
import json
import uuid


def change_uuids():
    path = 'temp/old_reports_temp'
    filenames = []
    for root, _d, files in os.walk(path):
        for file in files:
            print(file)
            if '.json' in file and file != 'metadata.json':
                filenames.append(os.path.join(root, file))
    new_slices = {}
    # change uuids for report slice files
    for filename in filenames:
        new_uuid = str(uuid.uuid4())
        with open(filename, 'r') as f:
            data = json.load(f)
            data['report_slice_id'] = new_uuid  # modify the report_slice_id
        new_name = '%s.json' % new_uuid
        new_file = os.path.join(os.getcwd()+'/temp/reports', new_name)
        with open(new_file, 'w') as f:
            json.dump(data, f, indent=4)
        new_slices[new_uuid] = {'number_hosts': len(data['hosts'])}  # used for metadata

    # change uuid for metadata.json
    metadata = ''
    new_uuid = str(uuid.uuid4())
    for root, _d, files in os.walk(path):
        for file in files:
            if file == 'metadata.json':
                metadata = os.path.join(root, file)
    with open(metadata, 'r') as f:
        data = json.load(f)
        data['report_id'] = new_uuid  # modify the report_id
        data['report_slices'] = new_slices
    with open('temp/reports/metadata.json', 'w') as f:
        json.dump(data, f, indent=4)


if __name__ == "__main__":
    change_uuids()
