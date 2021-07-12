# Verimatrix App Shield

This action integrates Verimatrix App Shield into your GitHub build workflow. It automates
the protection of your Android and iOS apps so you can run it whenever a new version 
of your application is built. 

Verimatrix App Shield is a zero-code in-app protection service. It protects your apps from 
reverse engineering and attack through a layered security approach. Protection layers include
obfuscation, environmental checks and binary integrity checks. 

A [Verimatrix App Shield](https://appshield.verimatrixcloud.net/) Pro account is required to use this Action. 

## Inputs

Action requires the following parameters: 

   * `api-key-id` -  APS api key id 
   * `api-key-secret` - APS api key secret
   * `app_file` -  mobile application file (_.zip_, _.apk_ or _aab_)

APS key id and APS key secret can be created and retrieved in [Verimatrix App Shield](https://appshield.verimatrixcloud.net/Developer)
portal under **My Account -> Developer** menu.  

## Outputs

Action produces a single output: 

   * `protected-file` - protected file name that was downloaded from APS. 

The `protected-file` name can be used with [upload-artifact](https://github.com/actions/upload-artifact) action
to save the file as a build artifact. 

## Usage

```yaml
- name: APS protection
  id: aps
  uses: verimatrix/app-shield-protect@v1
  with:
    api-key-id: ${{ secrets.APS_KEY_ID }}
    api-key-secret: ${{ secrets.APS_KEY_SECRET }}
    app-file: ${{ github.event.inputs.file }}
```
