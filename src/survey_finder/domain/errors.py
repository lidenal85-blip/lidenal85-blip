class NormalizationError(Exception):
    pass


class SchemaDriftError(NormalizationError):
    pass


class InvalidSurveyError(NormalizationError):
    pass
