class NoVcfsFoundException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class InvalidFileTypeError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class MetadataTemplateVersionException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class MetadataTemplateVersionNotFoundException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class SubmissionNotFoundException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class SubmissionStatusException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class SubmissionUploadException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DirLockError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class UserFileNotFoundException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DependencyNotFoundException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class WebinBadCredentialsException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class InvalidSubmissionException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DockerValidatorException(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)
