import argparse
import csv
import logging
import os
import subprocess
import time

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p', level='INFO')

container_image = 'eva_sub_cli'
container_validation_dir = '/opt/vcf_validation'
container_validation_output_dir = '/opt/vcf_validation/vcf_validation_output'


def run_command_with_output(command_description, command, return_process_output=True,
                            log_error_stream_to_output=False):
    process_output = ""

    logging.info(f"Starting process: {command_description}")
    logging.info(f"Running command: {command}")

    stdout = subprocess.PIPE
    # Some utilities output non-error messages to error stream. This is a workaround for that
    stderr = subprocess.STDOUT if log_error_stream_to_output else subprocess.PIPE

    with subprocess.Popen(command, stdout=stdout, stderr=stderr, bufsize=1, universal_newlines=True,
                          shell=True) as process:
        for line in iter(process.stdout.readline, ''):
            line = str(line).rstrip()
            logging.info(line)
            if return_process_output:
                process_output += line + "\n"
        if not log_error_stream_to_output:
            for line in iter(process.stderr.readline, ''):
                line = str(line).rstrip()
                logging.error(line)
    if process.returncode != 0:
        logging.error(f"{command_description} - failed! Refer to the error messages for details.")
        raise subprocess.CalledProcessError(process.returncode, process.args)
    else:
        logging.info(f"{command_description} - completed successfully")
    if return_process_output:
        return process_output


def check_if_file_missing(mapping_file):
    files_missing = False
    missing_files_list = []
    with open(mapping_file) as open_file:
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


def verify_docker_is_installed(docker):
    try:
        run_command_with_output("check docker is installed and available on the path", f"{docker} --version")
    except subprocess.CalledProcessError as ex:
        logging.error(ex)
        raise RuntimeError(f"Please make sure docker ({docker}) is installed and available on the path")


def verify_container_is_running(docker, container_name):
    container_run_cmd_ouptut = run_command_with_output("check if container is running", f"{docker} ps")
    if container_run_cmd_ouptut is not None and container_name in container_run_cmd_ouptut:
        logging.info(f"Container ({container_name}) is running")
        return True
    else:
        logging.info(f"Container ({container_name}) is not running")
        return False


def verify_container_is_stopped(docker, container_name):
    container_stop_cmd_ouptut = run_command_with_output("check if container is stopped", f"{docker} ps -a")
    if container_stop_cmd_ouptut is not None and container_name in container_stop_cmd_ouptut:
        logging.info(f"Container ({container_name}) is in stop state")
        return True
    else:
        logging.info(f"Container ({container_name}) is not in stop state")
        return False


def try_restarting_container(docker, container_name):
    logging.info(f"Trying to restart container {container_name}")
    try:
        run_command_with_output("Try restarting container", f"{docker} start {container_name}")
        if not verify_container_is_running(docker, container_name):
            raise RuntimeError(f"Container ({container_name}) could not be restarted")
    except subprocess.CalledProcessError as ex:
        logging.error(ex)
        raise RuntimeError(f"Container ({container_name}) could not be restarted")


def verify_image_available_locally(docker, container_image):
    container_images_cmd_ouptut = run_command_with_output("Check if validator image is present", f"{docker} images")
    if container_images_cmd_ouptut is not None and container_image in container_images_cmd_ouptut:
        logging.info(f"Container ({container_image}) image is available locally")
        return True
    else:
        logging.info(f"Container ({container_image}) image is not available locally")
        return False


def run_container(docker, container_name):
    logging.info(f"Trying to run container {container_name}")
    try:
        run_command_with_output("Try running container",
                                f"{docker} run -it --rm -d --name {container_name} {container_image}")
        # stopping execution to give some time to container to get up and running
        time.sleep(5)
        if not verify_container_is_running(docker, container_name):
            raise RuntimeError(f"Container ({container_name}) could not be started")
    except subprocess.CalledProcessError as ex:
        logging.error(ex)
        raise RuntimeError(f"Container ({container_name}) could not be started")


def download_container_image(docker, container_name):
    logging.info(f"Pulling container ({container_image}) image")
    try:
        run_command_with_output("pull container image", f"{docker} pull {container_image}")
        if not run_container(docker, container_name):
            raise RuntimeError(f"Container ({container_name}) could not be started")
    except subprocess.CalledProcessError as ex:
        logging.error(ex)
        raise RuntimeError(f"Cannot pull container ({container_image}) image")


def verify_docker_env(docker, container_name):
    verify_docker_is_installed(docker)

    if not verify_container_is_running(docker, container_name):
        if verify_container_is_stopped(docker, container_name):
            try_restarting_container(docker, container_name)
        else:
            if verify_image_available_locally(docker, container_image):
                run_container(docker, container_name)
            else:
                download_container_image(docker, container_name)


def copy_files_to_container(docker, container_name, mapping_file):
    run_command_with_output("Create directory structure for copying vcf metadata file into container",
                            f"{docker} exec {container_name} mkdir -p {container_validation_dir}/{os.path.dirname(mapping_file)}")
    run_command_with_output("Copy vcf metadata file to container",
                            f"{docker} cp {mapping_file} {container_name}:{container_validation_dir}/{mapping_file}")

    with open(mapping_file) as open_file:
        reader = csv.DictReader(open_file, delimiter=',')
        for row in reader:
            run_command_with_output("Create directory structure to copy vcf files into container",
                                    f"{docker} exec {container_name} "
                                    f"mkdir -p {container_validation_dir}/{os.path.dirname(row['vcf'])}")
            run_command_with_output("Copy vcf file to container",
                                    f"{docker} cp {row['vcf']} {container_name}:{container_validation_dir}/{row['vcf']}")
            run_command_with_output("Create directory structure to copy fasta files into container",
                                    f"{docker} exec {container_name} "
                                    f"mkdir -p {container_validation_dir}/{os.path.dirname(row['fasta'])}")
            run_command_with_output("Copy fasta file to container",
                                    f"{docker} cp {row['fasta']} {container_name}:{container_validation_dir}/{row['fasta']}")
            run_command_with_output("Create directory structure to copy assembly report files into container",
                                    f"{docker} exec {container_name} "
                                    f"mkdir -p {container_validation_dir}/{os.path.dirname(row['report'])}")
            run_command_with_output("Copy assembly report file to container",
                                    f"{docker} cp {row['report']} {container_name}:{container_validation_dir}/{row['report']}")


def run_docker_validator(docker, container_name, mapping_file, output_dir):
    # verify mapping file exists
    if not os.path.exists(mapping_file):
        raise RuntimeError(f'Mapping file {mapping_file} not found')

    # verify all files mentioned in metadata files exist
    files_missing, missing_files_list = check_if_file_missing(mapping_file)
    if files_missing:
        raise RuntimeError(f"some files (vcf/fasta) mentioned in metadata file could not be found. "
                           f"Missing files list {missing_files_list}")

    # check if docker container is ready for running validation
    verify_docker_env(docker, container_name)

    try:
        # remove all existing files from container
        run_command_with_output("Remove existing files from validation directory in container",
                                f"{docker} exec {container_name} rm -rf work {container_validation_dir}")

        # copy all required files to container (mapping file, vcf and fasta)
        copy_files_to_container(docker, container_name, mapping_file)

        # start validation
        run_command_with_output("Run Validation using Nextflow",
                                f"{docker} exec {container_name} nextflow run validation.nf "
                                f"--vcf_files_mapping {container_validation_dir}/{mapping_file} "
                                f"--output_dir {container_validation_output_dir}")

        # copy validation result to user host
        run_command_with_output("Copy validation output from container to host",
                                f"{docker} cp {container_name}:{container_validation_output_dir} {output_dir}")
    except subprocess.CalledProcessError as ex:
        logging.error(ex)


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

    run_docker_validator(docker_path, docker_container_name, args.vcf_files_mapping, args.output_dir)
