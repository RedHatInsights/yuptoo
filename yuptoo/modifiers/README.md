# Modifiers

Modifiers in yuptoo is used for modifying the host object(data) before sending it to host-inventory. Using modifiers it is possible to create, update or delete any property within host object or in system profile.

## How to create new modifiers

- Create a new file under yuptoo/modifiers/ and paste the below content in the file.
- Write a custom logic to modify the host object. 

```bash
from yuptoo.processor.utils import Modifier


class <ClassName>(Modifier):
    def run(self, host: dict, transformed_obj: dict, request_obj: dict):
        // Write your code below


```

That's it! yuptoo will do its magic to execute your modifier. :smile: