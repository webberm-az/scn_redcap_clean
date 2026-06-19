import argostranslate.package
import socket

from . import console


class TranslationPackages:
    ''' Manages downloading, installing, and caching local Argos language packages '''

    def __init__(self, to_code = 'en'):
        self.to_code = to_code
        self.loaded_langs = {'en'}
        self.local_packages = set()
        self.refresh_local_cache()
        self.failed_downloads = set()
        self.success_downloads = set()



    def ensure_lang_installed(self, from_code):
        ''' Checks if the language package is already loaded or installed '''
        from_code = self.normalize_from_code(from_code)
        if from_code in self.loaded_langs:
            return True

        if from_code in self.failed_downloads:
            return False
        
        if self.is_package_cached(from_code):
            return True
        
        success_install = self._download_and_install(from_code)

        return success_install



    def print_language_download_summary(self):
        self.get_already_downloaded_summary()
        self.get_success_download_summary()
        self.get_failed_download_summary()
        


    def get_already_downloaded_summary(self):
        if self.local_packages:
            self._print_local_packages()



    def get_success_download_summary(self):
        if self.success_downloads:
            self._print_new_downloads()



    def get_failed_download_summary(self):
        if self.failed_downloads:
            self._alert_internet_required()

    

    def refresh_local_cache(self):
        ''' Scans hard drive for packages already downloaded/installed '''
        try:
            self._is_package_installed()
        except Exception as error:
            self._alert_local_scan_failed_cache_set_to_empty(error)



    def normalize_from_code(self, from_code):
        # map codes for argostranslate.translate.translate()
        base_from_code = str(from_code).split('-')[0] # e.g. for 'zh-cn' base is zh
        
        return base_from_code



    def is_package_cached(self, from_code):
        ''' Checks if the package already installed '''
        is_match = (from_code, self.to_code) in self.local_packages
        if is_match:
            self.loaded_langs.add(from_code)
    
        return is_match



    def _download_and_install(self, from_code):
        ''' Downloads and installs packages '''
        package = self._get_remote_package(from_code)
        if not package:
            self.failed_downloads.add(from_code)
            return False
        
        is_download_success = self._is_download_success(from_code, package) #updates cache

        return is_download_success
    


    def _get_remote_package(self, from_code):
        ''' Updates package index and finds the matching remote package '''
        available_packages = self._try_get_agrotranslate_package(from_code)
        if not available_packages:
            return None

        for pkg in available_packages: 
            if self._is_matching_pkg(pkg, from_code):
                return pkg
    
        return None



    def _try_get_agrotranslate_package(self, from_code):
        try:
            argostranslate.package.update_package_index()
            available_packages = argostranslate.package.get_available_packages()
            return available_packages
        
        except Exception:
            self.failed_downloads.add(from_code)
            return None



    def _is_matching_pkg(self, pkg, from_code):
        ''' Confirms if a package matches the required language pair '''
        is_matching_pkg = (pkg.from_code == from_code and pkg.to_code == self.to_code)

        return is_matching_pkg



    def _is_download_success(self, from_code, package):
        try:
            self._try_install_remote_package(from_code, package)
            self._track_successful_download(from_code)
            return True
        
        except Exception:
            self.failed_downloads.add(from_code)
            return False



    def _try_install_remote_package(self, from_code, package):
        console.downloading_package_for(from_code)
        downloaded_file = package.download()
        argostranslate.package.install_from_path(downloaded_file)



    def _track_successful_download(self, from_code):
        self.refresh_local_cache() 
        self.success_downloads.add(from_code)
        self.loaded_langs.add(from_code)



    def _is_package_installed(self):
        installed_pkgs = argostranslate.package.get_installed_packages()
        self.local_packages = {(pkg.from_code, pkg.to_code) for pkg in installed_pkgs}



    def _alert_local_scan_failed_cache_set_to_empty(self, error):
        action = 'scan local Argos packages'
        console.failed_to(action, error)



    def _print_local_packages(self):
        local_packages = (from_code for from_code, _ in self.local_packages)
        langs = self._format_downloads_for_print(local_packages)
        console.translation_packages_summary('Local', langs)



    def _format_downloads_for_print(self, download_type):
        langs = ', '.join(sorted(download_type))

        return langs
    
    

    def _print_new_downloads(self):
        langs = self._format_downloads_for_print(self.success_downloads)
        console.translation_packages_summary('New', langs, 'downloaded')

    

    def _alert_internet_required(self):
        langs = self._format_downloads_for_print(self.failed_downloads)

        is_internet_available =  self._is_internet_available()
        console.alert_failed_translation_download(langs, is_internet_available)



    def _is_internet_available(self, host='8.8.8.8', port=53, timeout=3):
        try:
            socket.setdefaulttimeout(timeout)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.connect((host, port))
            return True
        except OSError:
            return False
