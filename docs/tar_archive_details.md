# Yuptoo specific tar archive

Yuptoo requires a specially formatted tar archive file. Files that do not conform to the required format will be marked as invalid and no processing will occur. The tar file must contain a metadata JSON file and one or more report slice JSON files. The file that contains metadata information is named metadata.json, while the files containing host data are named with their uniquely generated UUID4 report_slice_id followed by the .json extension.

      [root@fedora]$ tar -tf report_sat_6_9_beta.tar.gz
      ./
      ./metadata.json
      ./2dd60c11-ee5b-4ddc-8b75-d8d34de86a34.json
      ./eb45725b-165a-44d9-ad28-c531e3a1d9ac.json

## Yuptoo Meta-data JSON Format

Metadata should include information about the sender of the data, Host Inventory API version, and the report slices included in the tar file. Below is a sample metadata section for a report with 2 slices:

      {
         "report_id": "74d22f2c-e3c4-40a7-9cc9-f2b491e43666",
         "host_inventory_api_version": "1.0",
         "source": "Satellite",
         "source_metadata": {
            "foreman_rh_cloud_version": "3.0.14"
         },
         "report_slices": {
            "2dd60c11-ee5b-4ddc-8b75-d8d34de86a34": {
                  "number_hosts": 1
            },
            "eb45725b-165a-44d9-ad28-c531e3a1d9ac": {
                  "number_hosts": 1
            }
         }
      }


## Yuptoo Report Slice JSON Format

Report slices are a slice of the host inventory data for a given report. A slice limits the number of hosts to 10K. Slices with more than 10K hosts will be discarded as a validation error. Below is a sample report slice:

      {
         "report_slice_id":"2dd60c11-ee5b-4ddc-8b75-d8d34de86a34",
         "hosts":[
            {
               "fqdn":"vm255-51.gsslab.pnq2.redhat.com",
               "subscription_manager_id":"b35ad8ec-fdca-4e40-bc7a-f9f5db3155a0",
               "satellite_id":"b35ad8ec-fdca-4e40-bc7a-f9f5db3155a0",
               "bios_uuid":"25D6AD97-60FA-4D3E-B2CC-4AA437C28F71",
               "vm_uuid":"25D6AD97-60FA-4D3E-B2CC-4AA437C28F71",
               "ip_addresses":[
                  "10.74.255.51"
               ],
               "mac_addresses":[
                  "00:1a:4a:00:0a:8a"
               ],
               "system_profile":{
                  "number_of_cpus":1,
                  "number_of_sockets":1,
                  "cores_per_socket":1,
                  "system_memory_bytes":2184871936,
                  "network_interfaces":[
                     {
                        "ipv4_addresses":[
                           "10.74.255.51"
                        ],
                        "mac_address":"00:1a:4a:00:0a:8a",
                        "name":"ens3"
                     }
                  ],
                  "bios_vendor":"SeaBIOS",
                  "bios_version":"1.13.0-2.module+el8.2.1+7284+aa32a2c4",
                  "cpu_flags":[
                     "fpu",
                     "cpuid_fault",
                     "pti"
                  ],
                  "os_release":"Red Hat Enterprise Linux 8.3 (Ootpa)",
                  "os_kernel_version":"4.18.0-240.el8.x86_64",
                  "arch":"x86_64",
                  "subscription_status":"Unentitled",
                  "katello_agent_running":false,
                  "infrastructure_type":"virtual",
                  "installed_products":[
                     {
                        "name":"Red Hat Enterprise Linux for x86_64",
                        "id":"479"
                     }
                  ],
                  "installed_packages":[
                     "python3-dateutil-2.6.1-6.el8.noarch",
                     "subscription-manager-rhsm-certificates-1.27.16-1.el8.x86_64",
                     "iputils-20180629-2.el8.x86_64"
                  ],
                  "satellite_managed":true
               },
               "facts":[
                  {
                     "namespace":"satellite",
                     "facts":{
                        "satellite_version":"6.9.0 Beta",
                        "distribution_version":"8.3",
                        "satellite_instance_id":"7edd3e4f-b0e4-47c1-823a-cc095a148af0",
                        "is_simple_content_access":false,
                        "is_hostname_obfuscated":false,
                        "organization_id":1
                     }
                  }
               ],
               "tags":[
                  {
                     "namespace":"satellite",
                     "key":"satellite_instance_id",
                     "value":"7edd3e4f-b0e4-47c1-823a-cc095a148af0"
                  },
                  {
                     "namespace":"satellite",
                     "key":"lifecycle_environment",
                     "value":"Library"
                  },
                  {
                     "namespace":"satellite",
                     "key":"content_view",
                     "value":"Default Organization View"
                  },
                  {
                     "namespace":"satellite",
                     "key":"location",
                     "value":"Pune"
                  },
                  {
                     "namespace":"satellite",
                     "key":"organization",
                     "value":"RedHat"
                  },
                  {
                     "namespace":"satellite",
                     "key":"organization_id",
                     "value":"1"
                  }
               ]
            }
         ]
      }