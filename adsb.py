from math import *
from rtlsdr import RtlSdr
import time
import copy
import codecs
class ADSB:

	def __init__(self):
		self.sdr = RtlSdr()
		# configure device
		self.sdr.sample_rate = 2048e3  # Hz
		self.sdr.center_freq = 1.090e9    # Hz
		self.sdr.freq_correction = 20   # PPM
		self.sdr.gain = 50
		self.sdr.bandwidth=2048e3
		
	def module_carre(self,R,I):
		v = R**2+I**2
		return v

	def seuil(self,v):
		if v < 0.12:
			return 0
		else:
			return 1

	def boyer_moore(self,pat):   
		info= []
		j=[]
		i = 0
		while j!=pat and i < self.taille:
			if self.liste_bin[i] == pat[len(j)]:
				j.append(self.liste_bin[i])
			else:
				i=i-len(j)
				j=[]
			i+=1
		for y in range(self.taille-i):
			info.append(self.liste_bin[i+y])
		if j==pat:
			return info[0:214]

	def decode_manchester(self):      #CODE A TROUVER A140
		trame=[]
		motif=[1,0,1,0,0,0,0,1,0,1,0,0,0,0,0,0,1,0,0,1,0,1,0,1,1,0]
		self.trame = self.boyer_moore(motif)#[1,0,1,0,0,0,0,1,0,1,0,0,0,0,0,0]
		try:
			for i in range(0,107):
				trame.append(self.trame[2*i]) #On garde un échantillon sur deux
			return trame
		except:
			pass

	def lecture(self):
		self.liste_bin=[]
		self.trame=[]
		a = self.sdr.read_samples(2048)
		self.taille=len(a)
		for i in range(self.taille):			
			v=self.module_carre(a[i].real,a[i].imag)			
			self.liste_bin.append(self.seuil(v))
		if 	self.decode_manchester()!=None:	
			t1=[1,0,0,0,1]+self.decode_manchester()
			#if self.calcul_crc(t1)==0:
			self.trame=t1
	

	def get_ICAO(self):
		if self.trame!=None:
			return self.tradhex(self.trame[8:32])

	def get_trame(self):
		if self.trame!=None:	
			return self.trame

	def get_type(self):
		return self.bin2int(self.trame[32:37])

	def tradhex(self,liste):# fonction tradhex: convertir bin en hexadecimal
		list_string = map(str, liste)
		bin=''.join(list_string)
		decimal_representation = int(bin, 2)
		hextrad= hex(decimal_representation)
		return hextrad

	def bin2int(self,code): # fonction bin2int: convertir bin en decimal
		a=0
		if isinstance(code,list):
			for i in range(len(code)):
				a+=code[len(code)-i-1]*(2**i)
			return a
		else:
			return code

	def identification_vol(self):
		chars = '#ABCDEFGHIJKLMNOPQRSTUVWXYZ##### ###############0123456789######'
		csbin=self.trame[40:96]
		cs = ''
		cs += chars[self.bin2int(csbin[0:6])]
		cs += chars[self.bin2int(csbin[6:12])]
		cs += chars[self.bin2int(csbin[12:18])]
		cs += chars[self.bin2int(csbin[18:24])]
		cs += chars[self.bin2int(csbin[24:30])]
		cs += chars[self.bin2int(csbin[30:36])]
		cs += chars[self.bin2int(csbin[36:42])]
		cs += chars[self.bin2int(csbin[42:48])]
		cs = cs.replace('#', '')
		if len(cs)>3:
			return cs

	def calcul_crc(self,t):# fonction pour générer le CRC (vérification)
		GENERATOR = [1,1,1,1,1,1,1,1,1,1,1,1,1,0,1,0,0,0,0,0,0,1,0,0,1]
		for i in range(len(t)-24):
		# if 1, perform modulo 2 multiplication,
			if t[i] == 1:
				for j in range(len(GENERATOR)):
			# modulo 2 multiplication = XOR
					t[i+j] = t[i+j] ^ GENERATOR[j]
		# last 24 bits
		#print(t[-24:])
		return sum(t[-24:])

# Positions
# ---------------------------------------------

	def oe_flag(self):
		"""Check the odd/even flag. Bit 54, 0 for even, 1 for odd.
    	Returns:
        	int: 0 or 1, for even or odd frame
    	"""
		if self.get_type() > 4 and self.get_type() < 19:
			return self.trame[53]


	def cprlat(self):
		"""CPR encoded latitude
    	Returns:
        	int: encoded latitude
    	"""
		if self.get_type() > 4 and self.get_type() < 19:
			return self.bin2int(self.trame[54:71])

	def cprlon(self):
		"""CPR encoded longitude
		Returns:
		int: encoded longitude
    	"""
		if self.get_type() > 4 and self.get_type() < 19:
			return self.bin2int(self.trame[71:88])


	def position(self,trame0, trame1, t0, t1):
		"""if (5 <= self.get_type(msg0) <= 8 and 5 <= self.get_type(msg1) <= 8):
			return self.surface_position(msg0, msg1, t0, t1)
		"""
		if (9 <= self.get_type(trame0) <= 18 and 9 <= self.get_type(trame1) <= 18):
			return self.airborne_position(trame0, trame1, t0, t1)


	def airborne_position(self,trame0, trame1, t0, t1):
		"""Decode airborn position from a pair of even and odd position message
        131072 is 2^17, since CPR lat and lon are 17 bits each.
    Args:
        trame0 (list): even message (112 bits binary list)
        trame1 (list): odd message (112 bits binary list)
        t0 (int): timestamps for the even message
        t1 (int): timestamps for the odd message
    Returns:
        (float, float): (latitude, longitude) of the aircraft
    """


		cprlat_even = self.bin2int(trame0[54:71]) / 131072.0
		cprlon_even = self.bin2int(trame0[71:88]) / 131072.0
		cprlat_odd = self.bin2int(trame1[54:71]) / 131072.0
		cprlon_odd = self.bin2int(trame1[71:88]) / 131072.0

		air_d_lat_even = 360.0 / 60
		air_d_lat_odd = 360.0 / 59

    	# compute latitude index 'j'
		j = floor(59 * cprlat_even - 60 * cprlat_odd + 0.5)

		lat_even = float(air_d_lat_even * (j % 60 + cprlat_even))
		lat_odd = float(air_d_lat_odd * (j % 59 + cprlat_odd))

		if lat_even >= 270:
			lat_even = lat_even - 360

		if lat_odd >= 270:
			lat_odd = lat_odd - 360

    # check if both are in the same latidude zone, exit if not
		if self._cprNL(lat_even) != self._cprNL(lat_odd):
			return None

    # compute ni, longitude index m, and longitude
		if (t0 > t1):
			ni = self._cprN(lat_even, 0)
			m = floor(cprlon_even * (self._cprNL(lat_even)-1) -
                       cprlon_odd * self._cprNL(lat_even) + 0.5)
			lon = (360.0 / ni) * (m % ni + cprlon_even)
			lat = lat_even
		else:
			ni = self._cprN(lat_odd, 1)
		m = floor(cprlon_even * (self._cprNL(lat_odd)-1) -
                       cprlon_odd * self._cprNL(lat_odd) + 0.5)
		lon = (360.0 / ni) * (m % ni + cprlon_odd)
		lat = lat_odd

		if lon > 180:
			lon = lon - 360

		return round(lat, 5), round(lon, 5)


	def _cprN(self,lat, is_odd):
		nl = self._cprNL(lat) - is_odd
		return nl if nl > 1 else 1


	def _cprNL(self,lat):
		try:
			nz = 15
			a = 1 - cos(pi / (2 * nz))
			b = cos(pi / 180.0 * abs(lat)) ** 2
			nl = 2 * pi / (acos(1 - a/b))
			NL = floor(nl)
			return NL
		except:
		# happens when latitude is +/-90 degree
			return 1

	def altitude(self):
		"""Decode aircraft altitude
		Returns:
		int: altitude in feet
		"""
		if self.get_type() > 8 and self.get_type() < 19:
			q = self.trame[47]
			if q:
				n = self.bin2int(self.trame[40:47]+self.trame[48:52])
				alt = n * 25 - 1000
				return int(alt/3.2808)
			else:
				return None


	def nic(self):
		"""Calculate NIC, navigation integrity category

		Returns:
			int: NIC number (from 0 to 11), -1 if not applicable
		"""
		if self.get_type() > 8 and self.get_type() < 19:
			tc = self.get_type()
			nic_sup_b = self.bin2int(self.trame[39])

		if tc in [0, 18, 22]:
			nic = 0
		elif tc == 17:
			nic = 1
		elif tc == 16:
			if nic_sup_b:
				nic = 3
			else:
				nic = 2
		elif tc == 15:
			nic = 4
		elif tc == 14:
			nic = 5
		elif tc == 13:
			nic = 6
		elif tc == 12:
			nic = 7
		elif tc == 11:
			if nic_sup_b:
				nic = 9
			else:
				nic = 8
		elif tc in [10, 21]:
			nic = 10
		elif tc in [9, 20]:
			nic = 11
		else:
			nic = -1
		return nic


# ---------------------------------------------
# Velocity
# ---------------------------------------------

	def velocity(self):
		"""Calculate the speed, heading, and vertical rate
		Returns:
		(int, float, int, string): speed (kt), heading (degree),
            rate of climb/descend (ft/min), and speed type
            ('GS' for ground speed, 'AS' for airspeed)
    
		spd=0
		hdg=0
		rocd=0
		tag=None
		"""
		if self.get_type() == 19:
			subtype = self.bin2int(self.trame[37:40])

			if subtype in (1, 2):
				v_ew_sign = self.bin2int(self.trame[45])
				v_ew = self.bin2int(self.trame[46:56]) - 1       # east-west velocity

				v_ns_sign = self.bin2int(self.trame[56])
				v_ns = self.bin2int(self.trame[57:67]) - 1       # north-south velocity

				v_we = -1*v_ew if v_ew_sign else v_ew
				v_sn = -1*v_ns if v_ns_sign else v_ns
				spd = sqrt(v_sn*v_sn + v_we*v_we)  # unit in kts
				hdg = atan2(v_we, v_sn)
				hdg = degrees(hdg)                 # convert to degrees
				hdg = hdg if hdg >= 0 else hdg + 360    # no negative val
				tag = 'GS'

			else:
				hdg = self.bin2int(self.trame[46:56]) / 1024.0 * 360.0
				spd = self.bin2int(self.trame[57:67])
				tag = 'AS'

		vr_sign = self.bin2int(self.trame[68])
		vr = self.bin2int(self.trame[68:77])             # vertical rate
		rocd = -1*vr if vr_sign else vr         # rate of climb/descend

		return int(spd*1.851999999984), round(hdg, 1), int(rocd/3.28084), tag


	def speed_heading(self):
		"""Get speed and heading only from the velocity message
		Returns:
		(int, float): speed (kt), heading (degree)
	"""
		spd, hdg, rocd, tag = self.velocity()
		return spd, hdg


test= ADSB()
#test.lecture()
#print(test.identification_vol())
sauv_trame=[]
x=0


while True:
	test.lecture()
	
	if test.get_ICAO()!=None: # and test.calcul_crc(test.get_trame())==0x0
	#if len(test.get_trame())==112:
		#print(test.calcul_crc(test.get_trame()))
		#print(test.altitude())
		#if test.get_type()==19:
			#print(test.velocity())
		print(test.get_ICAO())
		print(test.get_type())
		print(test.identification_vol())
		if (test.calcul_crc(test.get_trame())==0):
			print ("trame valide")
			break
		else:
			print("trame non valide")
		ts = int(time.time())
		#print(len(test.get_trame()))

		test.get_trame().append(ts)
		
		if (9 <= test.get_type() <= 18):
			sauv_trame.append(test.get_trame())
		
			b=len(sauv_trame)
			#print(b)
			if b<50:
				for i in range (b-1):
					#print ('i='+str(i))
					#print('x='+str(x))
					if test.tradhex(sauv_trame[x][8:32])== test.tradhex(sauv_trame[i][8:32]) and sauv_trame[x][53]==0 and sauv_trame[i][53]==1 and b>2:
						print(test.airborne_position(sauv_trame[x], sauv_trame[i], sauv_trame[x][-1], sauv_trame[i][-1]))
						sauv_trame.pop(i)
						sauv_trame.pop(x-1)
						x-=2					
						break

					if x<b-1:
						x+=1	



