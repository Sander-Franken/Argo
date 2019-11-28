# Contains custom exception classes

class noAddressKey(Exception):
	# 400 Bad Request:
	# No key 'address' found in request body.
	pass

class emptyRequestBody(Exception):
	# 400
	# The request's body appears to be empty. Please supply an address.
	pass

class noAddressValue(Exception):
	# 400
	# The address value supplied appears to be empty.
	pass