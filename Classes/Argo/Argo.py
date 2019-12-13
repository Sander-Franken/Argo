import re
import json
import importlib
from itertools import tee

xcpt = importlib.import_module('.exceptions', 'Classes.Exceptions')


class Argo:
	def __init__(self, event):
		self.found_match = False
		self.method = ""
		self.result = ""
		self.response_body = {
			"found_match": False,
			"method": None,
			"result": None
		}

		self.event = event
		self.request_body = None
		self.address = None


	# This method goes through the address put in, in multiple passes from strict RegEx's likely to only match lat/lng information
	# to RegEx's more probable to match with other substrings as well.
	#
	# It will return whether a match was found (Boolean), the method used to find said match (string) and the coordinates
	# found (list containing strings).
	# The size of the list of coordinates returned could theoretically be anything greater than 0. It'll only have size 1 if the value
	# is deemed very likely to be a coordinate. Usually it will be size 2 and then it'll be very likely to contain a lat/lng.
	# 
	def findLatLng(self):
		self.fetchRequestBody()
		self.validateData()
		self.getAddress()
		
		self.result = (self.parseDMS_strict() or self.parseShortDMS() or self.parseDMS_relaxed() or self.parseDecimal())
		if not self.result:
			self.method = ''
		else:
			self.found_match = True

		self.response_body = {
			"found_match": self.found_match,
			"method": self.method,
			"result": self.result
		}

		return self.response_body


	# Fetches the data from the event
	def fetchRequestBody(self):
		self.event = json.loads(self.event)
		self.request_body = self.event["body"]


	# Validates the input, the body of the request. If it's not usable an error is raised.
	def validateData(self):
		address_found = False
		if self.request_body:
			for key, value in self.request_body.items():
				if key == 'address':
					address_found = True
					self.validateAddress(value)
					break
		else:
			raise xcpt.emptyRequestBody("The request's body appears to be empty. Please supply an address.", 400)

		if not address_found:
			raise xcpt.noAddressKey("No key 'address' found in request body.", 400)


	# Checks the value linked to the 'address' key in the request body. Raises an error if it's empty.
	def validateAddress(self, address):
		if not address:
			raise xcpt.noAddressValue("The address value supplied appears to be empty.", 400)


	# Loads the address value from the request into the class variable.
	def getAddress(self):
		self.address = self.request_body['address']


	# The regex used in this method is 'strict' in the sense that it is craft in such a way that any lat or lng it captures should actually
	# be a valid DMS coordinate. In testing this regex hasn't once returned a false positive.
	#
	# Regex used: [NSEW]?\s?(180|1[0-7][0-9]|[0-9]?[0-9])[°º](\s?[0-5]?[0-9][\'’]+)(\s?[0-5]?[0-9]([,\.][0-9]*)?["]?[‘’\']*)?\s?[NSEW]?
	def parseDMS_strict(self):
		result = ''
		self.method = 'DMS Strict'
		dmsRegEx = re.compile('[NSEW]?\s?(180|1[0-7][0-9]|[0-9]?[0-9])[°º](\s?[0-5]?[0-9][\'’]+)(\s?[0-5]?[0-9]([,\.][0-9]*)?["]?[‘’\']*)?\s?[NSEW]?')

		matches = re.finditer(dmsRegEx, self.address)
		matches, success_check = tee(matches)
		
		coords = []
		if list(success_check):
			for match in matches:#_iterable:
				coord = match.group(0)
				coords.append(coord.strip())
			if len(coords) == 2:						# If the regex matches with exactly 2 non-overlapping substrings, we assume they are a lat/lng pair.
				result = coords

			else:
				result = self.handleUnsures(coords)

		return result


	# The regex used in this method captures any lat/lng that is written in a sort of hybrid between DMS and Degrees that I've dubbed "shortDMS".
	# There's probably another name for it, I imagine. Pairs look like this: 45°4332N 005°0452E.
	#
	# Regex used: \d{1,3}[°º]\d{4}\s?[NSEW]
	def parseShortDMS(self):
		result = ''
		self.method = 'DMS Short'
		shortDmsRegEx = re.compile('\d{1,3}[°º]\d{4}\s?[NSEW]')

		matches = re.finditer(shortDmsRegEx, self.address)
		matches, success_check = tee(matches)

		coords = []
		if list(success_check):
			for match in matches:
				coord = match.group(0)
				coords.append(coord.strip())
			if len(coords) == 2:
				result = coords

			else:
				result = self.handleUnsures(coords)

		return result


	# The regex used in this method is more "relaxed": it assumes that any set of 3 groups of 2-3 numbers, with one having decimals, and perhaps
	# a letter out of [NSEW] at the front or end is a latitude or longitude in DMS-notation. Since the strings we're parsing are addresses,
	# this is very likely to be the case. 
	#
	# Regex used: [NSEW]?\s?\d{1,3} \d{1,2} \d{1,2}\.\d+\s?[NSEW]?
	def parseDMS_relaxed(self):
		result = ''
		self.method = 'DMS Relaxed'
		relaxedDmsRegEx = re.compile('[NSEW]?\s?\d{1,3} \d{1,2} \d{1,2}\.\d+\s?[NSEW]?')

		matches = re.finditer(relaxedDmsRegEx, self.address)
		matches, success_check = tee(matches)

		coords = []
		if list(success_check):
			for match in matches:
				coord = match.group(0)
				coords.append(coord.strip())
			if len(coords) == 2:
				result = coords

			else:
				result = self.handleUnsures(coords)

		return result


	# The regex used in this method will capture any decimal number (only with "." as decimal separator) that falls within a valid
	# range to be a latitude or longitude coordinate. This means that it will relatively often capture other numbers that may be
	# in an address (ex. in "7.5 KM from Highway 3" it will capture the "7.5"). Therefor additional checks are required to make sure
	# if or which of the captured numbers are lat/lngs.
	#
	# Regex used: (?:([+-]?([1-8]?[0-9])(\.[0-9]+)|90(\.0+))|([+-]?((180(\.0+))|((1[0-7][0-9])|([0-9]{1,2}))\.[0-9]+)))
	def parseDecimal(self):
		result = ''
		self.method = 'Decimal'
		decimalRegEx = re.compile('(?:([+-]?([1-8]?[0-9])(\.[0-9]+)|90(\.0+))|([+-]?((180(\.0+))|((1[0-7][0-9])|([0-9]{1,2}))\.[0-9]+)))')

		matches = re.finditer(decimalRegEx, self.address)		
		matches, success_check = tee(matches)

		coords = []
		if list(success_check):
			coords = self.cardinalDirectionCheck()
			if coords:						# cardinal coords were found
				cardinal_coords = coords
				regular_coords = []
				for match in matches:
					coord = match.group(0)
					regular_coords.append(coord.strip())

				if len(cardinal_coords) == len(regular_coords):				# possible that the regular regex picked up another decimal number as well or only one of the coordinates has a cardinal direction
					coords = cardinal_coords

				else:
					coords = self.replaceRegWithCardCoords(regular_coords, cardinal_coords)
			else:							# cardinal coords weren't found
				for match in matches:
					coord = match.group(0)
					coords.append(coord.strip())

			coords = self.ipAddressCheck(coords)
			if coords:
				if len(coords) == 2:
					result = coords

				else:
					result = self.handleUnsures(coords)

		return result


	# This method is used to check if a decimal lat/lng has a cardinal direction (North/South/East/West) after it. If the cardinal direction is South or
	# West, this means effectively the same as putting a "-" in front of the lat/lng, so it's important to know if it's there.
	# I have not encountered cases where the cardinal direction was in front of the lat/lng. Checking for that is also much more prone to error by capturing
	# parts of other words or accidentally grabbing the direction belonging to the latitude when capturing the longitude.
	#
	# The reason the optional degree symbol is there is that I've found that it is occasionally used in decimal lat/lngs when cardinal directions are present.
	#
	# Regex used: (?:([+-]?([1-8]?[0-9])(\.[0-9]+)|90(\.0+))|([+-]?((180(\.0+))|((1[0-7][0-9])|([0-9]{1,2}))\.[0-9]+)))[°º]?\s?[NSEW]([\s,.]|$)
	def cardinalDirectionCheck(self):
		cardinalEndRegex = re.compile('(?:([+-]?([1-8]?[0-9])(\.[0-9]+)|90(\.0+))|([+-]?((180(\.0+))|((1[0-7][0-9])|([0-9]{1,2}))\.[0-9]+)))[°º]?\s?[NSEW]([\s,.]|$)')
		matches = re.finditer(cardinalEndRegex, self.address)
		matches, success_check = tee(matches)

		coords = []
		if list(success_check):
			for match in matches:
				coord = match.group(0).strip()
				if coord[-1] == "," or coord[-1] == ".":
					coord = coord[:-1]
				coords.append(coord)

			return coords

		else:
			return []
		

	# Here we go through the lists of coordinates found by the regular Decimal and Cardinal decimal regex's. It replaces the instances in the regular
	# list with their cardinal counterparts and return the updated list.
	# It uses the fact that a cardinal coord will always be 1-4 characters longer than its regular counterpart to filter it out of the list.
	def replaceRegWithCardCoords(self, regular_coords, cardinal_coords):
		replacements = []
		for reg_coord in regular_coords:
			regex = reg_coord + '.{1,4}'			
			for card_coord in cardinal_coords:
				if re.match(regex, card_coord):
					replacements.append((reg_coord, card_coord))

		for reg_coord,card_coord in replacements:
			index = regular_coords.index(reg_coord)
			regular_coords[index] = card_coord

		return regular_coords


	# Here we check if there is an IP address in the address. Because of the dots in an IP address, parts of it can be picked up by the Decimal Regex.
	# If the list of coords contains any that correspond to a part of the IP address found, they are removed.
	#
	# Regex used: ((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)
	def ipAddressCheck(self, coords):
		ipAddressRegEx = re.compile('((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)')
		ip = re.search(ipAddressRegEx, self.address)

		if ip:
			ip = ip.group(0)
			new_coords = []
			for coord in coords:
				if coord in ip:
					pass
				else:
					new_coords.append(coord)

			return new_coords

		else:
			return coords


	# This method takes care of the times where one of the RegEx's (Should almost exclusively be the Decimal RegEx) finds 1 or more than 2 values.
	# It uses the indicator checkers to try and determine for each coord if it is an actual coord or a distance-number.
	# Depending on the results of those checks it will return 1 or 2 coordinates, the whole original result from the RegEx or an empty string to indicate
	# there are pretty surely no coordinates in the address.
	def handleUnsures(self, coords):
		gps_indicateds = []
		distance_indicateds = []

		for coord in coords:
			if self.hasNearbyGpsIndicator(coord):
				gps_indicateds.append(coord)

			if self.hasNearbyDistanceIndicator(coord):
				distance_indicateds.append(coord)

		if len(gps_indicateds) == 2:
			return gps_indicateds

		elif len(distance_indicateds) == len(coords):
			return ''

		elif len(gps_indicateds) == len(coords) == 1:
			return gps_indicateds

		elif (len(coords) - len(distance_indicateds)) == 2:
			for coord in distance_indicateds:
				coords.remove(coord)
			return coords

		elif len(coords) == 1:
			return ''

		else:
			return coords


	# This method returns True if in the vicinity of the coord in the address is some indicator that implies the number is actually a coordinate.
	def hasNearbyGpsIndicator(self, coord):
		gps_indicators = ['latitude', 'lat', 'longitude', 'lon', 'gps', 'coord', 'coordinate']

		address = self.address.lower()
		coord_start_index = address.index(coord)
		coord_end_index = coord_start_index + len(coord)

		for indicator in gps_indicators:
			if indicator in address:
				search_index = 0
				found = False
				for i in range(address.count(indicator)):			# There may be multiple occurances of for example 'lon' in an address
					ind_start_index = address.index(indicator, search_index)		
					ind_len = len(indicator)

					dif_front = coord_start_index - ind_start_index - ind_len
					dif_back = ind_start_index - coord_end_index
					
					if dif_front < 3 and dif_front > 0:  			# -3 to allow for both a space and ':' to be inbetween.
						found = True
						break
						
					elif dif_back < 2 and dif_back > 0:				# Unlikely to happen and there should really only be a space inbetween at max.
						found = True
						break
					
					search_index = search_index + ind_len

				if found:
					return True

		return False 											# In case no indicators are found at all.


	# This method returns True if in the vicinity of the coord in the address is some indicator that implies the number is actually some measure
	# of distance rather than a coordinate.
	def hasNearbyDistanceIndicator(self, coord):
		distance_indicators = ['km', 'mile']

		coord_start_index = self.address.index(coord)
		coord_end_index = coord_start_index + len(coord)

		address = self.address.lower()
		for indicator in distance_indicators:
			if indicator in address:
				search_index = 0
				found = False
				for i in range(address.count(indicator)):			# There may be multiple occurances of for example 'km' in an address
					ind_start_index = address.index(indicator, search_index)		
					ind_len = len(indicator)

					dif_front = coord_start_index - ind_start_index - ind_len
					dif_back = ind_start_index - coord_end_index 
					
					if dif_front < 3 and dif_front > 0:  			# -3 to allow for both a space and ':' to be inbetween.
						found = True
						break
						
					elif dif_back < 2 and dif_back > 0:				# Unlikely to happen and there should really only be a space inbetween at max.
						found = True
						break
					
					search_index = search_index + ind_len

				if found:
					return True

		return False 											# In case no indicators are found at all.

