from . import utils



def custom_alert(type, message):
    print(f"\n| {type} | {message}\n")

def alert_missing_config_file(
    dir, role_name, set_config, file_path = '', message = None):
    type = f"{role_name} Missing"
    custom_alert(type, file_path)
    print(f"set filename using  {set_config} = 'your_file_name'  and store in  '{dir}' folder\n")
    if message:
        alternative(message)

def alternative(message):
    print("\n ``Alternatively, {message} \n")



#       Error

def error(message):
    custom_alert('Error', message)

def error_missing(missing_obj, message):
    text = f"'{missing_obj}' {message}"
    custom_alert('Error', text)

def error_filepath_DNE(file_path):
    error_missing(file_path, 'does not exist.')


#       Info

def info(message):
    custom_alert('Info', message)

def file_saved(filename, file_path):
    message = f"'{filename}' txt file saved to: {file_path}"
    info(message)

def info_missing_file(name, folder):
    message = f"{name} not found in {folder} folder"
    info(message)

def missing_override(override_filename, override_description, proceeding_message):
    info_missing_file(override_filename, 'overrides')
    print(f'No {override_description} performed.\n'\
        f'Proceeding {proceeding_message}\n')



#       Alert

def alert(message):
    custom_alert('Alert', message)

def alert_missing_file(name, path):
    message = f"{name} not found at: {path}"
    alert(message)



#       Action to Path

def action_to_path(action, path):
    print(f"{action} to: {path}")

def file_saved_to(file, path):
    action = f"'{file}' file saved"
    action_to_path(action, path)

def archive_file_saved_to(path):
    action = " ( Archive version saved as read-only"
    action_to_path(action, f"{path} )\n")



#       Failed to:

def failed_to(action, error):
    print(f'Failed {action}: {error}')



#       Downloading for:

def downloading_package_for(name):
    print(f'Downloading remote package for {name}...')




#       TXT viewer

def view_txt_file(filename, output_dir):
    '''
    Reads a text file and prints its entire contents to the console.
    '''
    file_path = utils.get_txt_filepath(filename, output_dir)
    if not file_path.exists():
        error_filepath_DNE(file_path)
    else:
        txt_content(filename, file_path)


def txt_content(filename, file_path):
    print(f'\n   |  {filename}  |\n\n')
    print(file_path.read_text(encoding='utf-8'))
    print('\n`    `    `    `    `    `    `    `    `\n')

    


#     Argos prints

def translation_packages_summary(type, language_list, status=""):
    if_status = f" {status}" if status else ''
    message = f"{type} ArgosTranslate package(s){if_status} | Language(s): {language_list}"
    info(message)


def alert_failed_translation_download(language_list, internet_available = True):
    message = f"Failed ArgosTranslate download(s) | Language(s): {language_list}"
    alert(message)
    if not internet_available:
        info(' Internet required for new downloads\n')
