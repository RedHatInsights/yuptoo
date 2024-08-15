# Yuptoo (Yupana Upload Processor II)

Yuptoo is a rewrite of Yupana service. Below are the key differences and improvements made in yuptoo. 

* No Database - database dependence has been completely removed.
* No multi-threading.
* No explicit state-machine.
* Reduced iteration over the report/hosts. Yuptoo has single iteration for validation and modification.
* Removed django or any other http service.
* Made yuptoo more modular and pluggable. check [README.md](https://github.com/RedHatInsights/yuptoo/blob/main/yuptoo/modifiers/README.md)
* Increased code coverage.
* Less dependent on third party packages.