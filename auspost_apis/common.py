class AusPostException(Exception):

    def __init__(self, code, msg):
        self.code = code
        self.message = msg
        super(AusPostException, self).__init__(self.get_error_message())

    def get_error_message(self):
        return u"Error %d: %s" % (self.code, self.message)
