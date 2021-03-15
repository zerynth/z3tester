


def update_headers(f):
    def inner(self, *args, **kwargs):
        if 'HttpHeaders' in self._general_configs:
            if not kwargs.get('headers'):
                kwargs['headers'] = self._general_configs['HttpHeaders']
            else:
                kwargs['headers'].update(self._general_configs['HttpHeaders'])
        return f(self, *args, **kwargs)
    return inner