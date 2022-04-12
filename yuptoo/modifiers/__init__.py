import pkgutil

modules = []
for loader, module_name, is_pkg in pkgutil.walk_packages(__path__):
    modules.append(module_name)


def get_modifiers():
    return modules
