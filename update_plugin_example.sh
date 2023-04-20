cd plugin_profiles/built-in/iot2.dueros.com/
rm test.zip
zip -r test.zip  prompt  api.yaml  manifest.json  device_list.json devicelist_detail.txt
cd -
cp plugin_profiles/built-in/iot2.dueros.com/test.zip static/plugin_example.zip



cd plugin_profiles/built-in/iot3.dueros.com/
rm test.zip
zip -r test.zip  prompt  api.yaml  manifest.json  device_list.json devicelist_detail.txt
cd -
cp plugin_profiles/built-in/iot3.dueros.com/test.zip static/plugin_example_iot3.zip
