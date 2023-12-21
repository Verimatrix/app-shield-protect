# Verimatrix XTD and Counterspy

This action integrates Verimatrix Extended Threat Defense and Counterspy into your GitHub build workflow. It automates
the protection of your Android and iOS apps so you can run it whenever a new version 
of your application is built. 

[Verimatrix XTD and Counterspy](https://portal.platform.verimatrixcloud.net/) are a zero-code in-app protection services. They protect your apps from
reverse engineering and attack through a layered security approach. Protection layers include
obfuscation, environmental checks and binary integrity checks. 

All **XTD** subscription tiers support this action, while for **Counterspy** you need a Standard subscription.

## Inputs

Action requires the following parameters: 

   * `api-key-id` -  api key ID
   * `api-key-secret` - api key secret
   * `app_file` -  mobile application file (_.zip_, _.apk_ or _aab_)

Key ID and key secret can be created and retrieved in [XTD or Counterspy](https://portal.platform.verimatrixcloud.net/)
portal under "Settings" menu, in the "API Key Manager" panel. Simply click the
"Generate New API Key" button for generating a new key.

## Outputs

Action produces a single output: 

   * `protected-file` - protected file name that was downloaded from APS. 

The `protected-file` name can be used with [upload-artifact](https://github.com/actions/upload-artifact) action
to save the file as a build artifact. 

## Usage

```yaml
- name: Application Protection
  id: app-protect
  uses: verimatrix/app-protect@v2
  with:
    api-key-id: ${{ secrets.API_KEY_ID }}
    api-key-secret: ${{ secrets.API_KEY_SECRET }}
    app-file: ${{ github.event.inputs.file }}
```
