cd plugin_profiles/built-in/iot2.dueros.com/
zip -r test.zip  prompt  api.yaml  manifest.json  device_list.json
cd -
cp test.zip upload/plugin_example.zip
