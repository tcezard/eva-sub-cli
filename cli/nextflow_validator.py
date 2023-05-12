import argparse
import csv
import logging
import os
import subprocess
import time

from cli.docker_validator import run_command_with_output
from cli.reporter import Reporter

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level='INFO')

container_image = 'eva_sub_cli'
container_validation_dir = '/opt/vcf_validation'
container_validation_output_dir = '/opt/vcf_validation/vcf_validation_output'


class DockerReporter(Reporter):

    def __init__(self, mapping_file, output_dir, container_name=container_image, docker_path='docker'):
        self.docker_path = docker_path
        self.mapping_file = mapping_file
        self.container_name = container_name
        super().__init__(self._find_vcf_file(), output_dir)

    def _validate(self):
        cfg['executable']['python']['script_path'] = os.path.dirname(os.path.dirname(__file__))
        validation_config = {
            'vcf_files_mapping': vcf_files_mapping_csv,
            'output_dir': output_dir,
            'executable': cfg['executable'],
            'validation_tasks': validation_tasks
        }
        # run the validation
        validation_confg_file = os.path.join(self.eload_dir, 'validation_confg_file.yaml')
        with open(validation_confg_file, 'w') as open_file:
            yaml.safe_dump(validation_config, open_file)
        validation_script = os.path.join(NEXTFLOW_DIR, 'validation.nf')
        try:
            run_command_with_output(
                'Nextflow Validation process',
                f"nextflow run {validation_script} "
                f"--vcf_files_mapping {container_validation_dir}/{self.mapping_file} "
                f"--output_dir {output_dir}"
            )
        except subprocess.CalledProcessError:
            self.error('Nextflow pipeline failed: results might not be complete')
        return output_dir

    def _find_vcf_file(self):
        vcf_files = []
        with open(self.mapping_file) as open_file:
            reader = csv.DictReader(open_file, delimiter=',')
            for row in reader:
                vcf_files.append(row['vcf'])
        return vcf_files

    def run_validator(self):
        # verify mapping file exists
        if not os.path.exists(self.mapping_file):
            raise RuntimeError(f'Mapping file {self.mapping_file} not found')

        # verify all files mentioned in metadata files exist
        files_missing, missing_files_list = self.check_if_file_missing()
        if files_missing:
            raise RuntimeError(f"some files (vcf/fasta) mentioned in metadata file could not be found. "
                               f"Missing files list {missing_files_list}")

        # check if docker container is ready for running validation
        self.verify_docker_env()

        try:
            # remove all existing files from container
            run_command_with_output(
                "Remove existing files from validation directory in container",
                f"{self.docker_path} exec {self.container_name} rm -rf work {container_validation_dir}"
            )

            # copy all required files to container (mapping file, vcf and fasta)
            self.copy_files_to_container()

            # start validation
            run_command_with_output("Run Validation using Nextflow",
                                    f"{self.docker_path} exec {self.container_name} nextflow run validation.nf "
                                    f"--vcf_files_mapping {container_validation_dir}/{self.mapping_file} "
                                    f"--output_dir {container_validation_output_dir}")

            # copy validation result to user host
            run_command_with_output(
                "Copy validation output from container to host",
                f"{self.docker_path} cp {self.container_name}:{container_validation_output_dir} {self.output_dir}"
            )
        except subprocess.CalledProcessError as ex:
            logging.error(ex)

    def check_if_file_missing(self):
        files_missing = False
        missing_files_list = []
        with open(self.mapping_file) as open_file:
            reader = csv.DictReader(open_file, delimiter=',')
            for row in reader:
                if not os.path.exists(row['vcf']):
                    files_missing = True
                    missing_files_list.append(row['vcf'])
                if not os.path.exists(row['fasta']):
                    files_missing = True
                    missing_files_list.append(row['fasta'])
                if not os.path.exists(row['report']):
                    files_missing = True
                    missing_files_list.append(row['report'])

        return files_missing, missing_files_list

    def verify_docker_is_installed(self):
        try:
            run_command_with_output(
                "check docker is installed and available on the path",
                f"{self.docker_path} --version"
            )
        except subprocess.CalledProcessError as ex:
            logging.error(ex)
            raise RuntimeError(f"Please make sure docker ({self.docker_path}) is installed and available on the path")

    def verify_container_is_running(self):
        container_run_cmd_ouptut = run_command_with_output("check if container is running", f"{self.docker_path} ps")
        if container_run_cmd_ouptut is not None and self.container_name in container_run_cmd_ouptut:
            logging.info(f"Container ({self.container_name}) is running")
            return True
        else:
            logging.info(f"Container ({self.container_name}) is not running")
            return False

    def verify_container_is_stopped(self):
        container_stop_cmd_ouptut = run_command_with_output(
            "check if container is stopped",
            f"{self.docker_path} ps -a"
        )
        if container_stop_cmd_ouptut is not None and self.container_name in container_stop_cmd_ouptut:
            logging.info(f"Container ({self.container_name}) is in stop state")
            return True
        else:
            logging.info(f"Container ({self.container_name}) is not in stop state")
            return False

    def try_restarting_container(self):
        logging.info(f"Trying to restart container {self.container_name}")
        try:
            run_command_with_output("Try restarting container", f"{self.docker_path} start {self.container_name}")
            if not self.verify_container_is_running():
                raise RuntimeError(f"Container ({self.container_name}) could not be restarted")
        except subprocess.CalledProcessError as ex:
            logging.error(ex)
            raise RuntimeError(f"Container ({self.container_name}) could not be restarted")

    def verify_image_available_locally(self):
        container_images_cmd_ouptut = run_command_with_output(
            "Check if validator image is present",
            f"{self.docker_path} images"
        )
        if container_images_cmd_ouptut is not None and container_image in container_images_cmd_ouptut:
            logging.info(f"Container ({container_image}) image is available locally")
            return True
        else:
            logging.info(f"Container ({container_image}) image is not available locally")
            return False

    def run_container(self):
        logging.info(f"Trying to run container {self.container_name}")
        try:
            run_command_with_output(
                "Try running container",
                f"{self.docker_path} run -it --rm -d --name {self.container_name} {container_image}"
            )
            # stopping execution to give some time to container to get up and running
            time.sleep(5)
            if not self.verify_container_is_running():
                raise RuntimeError(f"Container ({self.container_name}) could not be started")
        except subprocess.CalledProcessError as ex:
            logging.error(ex)
            raise RuntimeError(f"Container ({self.container_name}) could not be started")

    def download_container_image(self):
        logging.info(f"Pulling container ({container_image}) image")
        try:
            run_command_with_output("pull container image", f"{self.docker_path} pull {container_image}")
            if not self.run_container():
                raise RuntimeError(f"Container ({self.container_name}) could not be started")
        except subprocess.CalledProcessError as ex:
            logging.error(ex)
            raise RuntimeError(f"Cannot pull container ({container_image}) image")

    def verify_docker_env(self):
        self.verify_docker_is_installed()

        if not self.verify_container_is_running():
            if self.verify_container_is_stopped():
                self.try_restarting_container()
            else:
                if self.verify_image_available_locally():
                    self.run_container()
                else:
                    self.download_container_image()

    def copy_files_to_container(self):
        run_command_with_output(
            "Create directory structure for copying vcf metadata file into container",
            (f"{self.docker_path} exec {self.container_name} "
             f"mkdir -p {container_validation_dir}/{os.path.dirname(self.mapping_file)}")
        )
        run_command_with_output(
            "Copy vcf metadata file to container",
            (f"{self.docker_path} cp {self.mapping_file} "
             f"{self.container_name}:{container_validation_dir}/{self.mapping_file}")
        )

        with open(self.mapping_file) as open_file:
            reader = csv.DictReader(open_file, delimiter=',')
            for row in reader:
                run_command_with_output(
                    "Create directory structure to copy vcf files into container",
                    (f"{self.docker_path} exec {self.container_name} "
                     f"mkdir -p {container_validation_dir}/{os.path.dirname(row['vcf'])}")
                )
                run_command_with_output(
                    "Copy vcf file to container",
                    f"{self.docker_path} cp {row['vcf']} {self.container_name}:{container_validation_dir}/{row['vcf']}"
                )
                run_command_with_output(
                    "Create directory structure to copy fasta files into container",
                    (f"{self.docker_path} exec {self.container_name} "
                     f"mkdir -p {container_validation_dir}/{os.path.dirname(row['fasta'])}")
                )
                run_command_with_output(
                    "Copy fasta file to container",
                    (f"{self.docker_path} cp {row['fasta']} "
                     f"{self.container_name}:{container_validation_dir}/{row['fasta']}")
                )
                run_command_with_output(
                    "Create directory structure to copy assembly report files into container",
                    (f"{self.docker_path} exec {self.container_name} "
                     f"mkdir -p {container_validation_dir}/{os.path.dirname(row['report'])}")
                )
                run_command_with_output(
                    "Copy assembly report file to container",
                    (f"{self.docker_path} cp {row['report']} "
                     f"{self.container_name}:{container_validation_dir}/{row['report']}")
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run pre-submission validation checks on VCF files', add_help=False)
    parser.add_argument("--docker_path", help="Full path to the docker installation, "
                                              "not required if docker is available on path", required=False)
    parser.add_argument("--container_name", help="Name of the docker container", required=False)
    parser.add_argument("--vcf_files_mapping",
                        help="csv file with the mappings for vcf files, fasta and assembly report", required=True)
    parser.add_argument("--output_dir", help="Directory where the validation output reports will be made available",
                        required=True)
    args = parser.parse_args()

    docker_path = args.docker_path if args.docker_path else 'docker'
    docker_container_name = args.container_name if args.container_name else container_image

    validator = DockerReporter(args.vcf_files_mapping, args.output_dir, docker_container_name, docker_path)
    validator.validate()
