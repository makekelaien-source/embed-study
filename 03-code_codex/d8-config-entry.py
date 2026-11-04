import d8_config_tools

expected = {"pump": 10}
actual = {"pump": 12, "fan": 20}
dictionary = d8_config_tools.check_config(expected,actual)
print(dictionary)
