from urllib.request import urlopen
from urllib.parse import urlencode
from hashlib import md5
from random import choice, randint
from string import ascii_uppercase, digits 

API_VER = '1.1.8'

if API_VER == '1.1.7':
    API_BASE = 'http://ocrhood.gazcad.com/'
else:
    API_BASE = 'http://www.captchabrotherhood.com/'
RECAPTCHA_BASE = 'http://www.google.com/recaptcha/api/image?c='
ARRAY_IF = [1, 1, 1, 1, 1, 1, -1, 1, 1, 1, 1, 1, 1, -1, 1, 1]
ARRAY_A = [1, 1, -1, 1, 1, -1, -1, 1, 1, -1, 1, -1, -1, -1, 1, 1]
ARRAY_B = [1, -1, -1, 1, -1, -1, 1, 1, 1, -1, 1, 1, -1, 1, 1, -1]

class BrotherhoodException(Exception):
    pass

class Challange:
    
    def __init__(self, brotherhood, cid):
        self.brotherhood = brotherhood
        self.cid = cid
        self.image = None
        
    def _md5(self, text):
        code = text.strip()+"CBH"
        code = md5(code.encode()).hexdigest()
        return code[-8:]
        
    def _checksum(self, cidCode):
        check = abs(sum([ord(cidCode[i])*ARRAY_IF[i] for i in range(15)])+int(ord(cidCode[15])/16))%10
        if check%2 == 1: 
            return str(abs(sum([ord(cidCode[i])*ARRAY_A[i] for i in range(15)])+int(ord(cidCode[15])/16)))
        else: 
            return str(abs(sum([ord(cidCode[i])*ARRAY_B[i] for i in range(15)])-int(ord(cidCode[15])/16)))
    
    def add_user(self, captcha_answer, username, password, email=''):
        nameCode = self._md5(username)
        cidCode = ''.join(choice(ascii_uppercase + digits) for x in range(randint(16, 25)))
        cidCode = cidCode+'_'+self._checksum(cidCode)
        print(cidCode)         
        args = {
                'username': username,
                'password': password,
                'email': email,
                'cCode': nameCode,
                'challange': self.cid,
                'answer': captcha_answer,
                'cid': cidCode, 
                }    
                
        self.brotherhood.call('createUser', args, default_args=False)    
        #OK:User added
        #Invalid captcha answer
        #Username already taken
        #Invalid characters
	   #Error:User error 2 ?ban

    def get_image(self):
        if not self.image:
            self.image = self.fetch_image()
        return self.image

    def fetch_image(self):
        return self.call_recaptcha(self.cid)
        
    def call_recaptcha(self, image_url):
        url = '%s%s' % (RECAPTCHA_BASE, image_url) 
    
        return urlopen(url).read()   
        
class Captcha:

    def __init__(self, brotherhood, cid):
        self.brotherhood = brotherhood
        self.cid = cid
        self.image = None

    def solve(self, answer):
        args = {
                'captchaID': self.cid,
                'captchaAnswer': answer,
                }

        self.brotherhood.call('setCaptchaResult', args, True)
        

    def get_image(self):
        if self.image:
            return self.image
        else:
            self.image = self.fetch_image()
            return self.image

    def fetch_image(self):
        args = {
                'captchaID': self.cid,
                }

        return self.brotherhood.call('showcaptcha', args, True)
         

class Brotherhood:

    def __init__(self, user, password):
        self.user = user
        self.password = password

    def call(self, method_name, args={}, binary=False, default_args=True):
        if default_args:
            args['username'] = self.user
            args['password'] = self.password
            args['version'] = API_VER

        query = urlencode(args)

        url = '%s%s.aspx?%s' % (API_BASE, method_name, query)
        
        response = urlopen(url)

        if binary:
            return response.read()
        else:
            data = response.read().decode('utf-8')
            status = data[:2]

            if status == 'OK':
                return data[3:]
            else:
                raise BrotherhoodException(data)
                    

    def get_captcha(self):
        result = self.call('getCaptcha2Solve')

        if result == 'No Captcha':
            return None
        else:
            return Captcha(self, result)

    def get_credits(self):
        return int(self.call('askCredits'))

    def get_challange(self):
        result = self.call('svcGetChallangeCode', binary=True, default_args=False).decode('utf-8')
        
        return Challange(self, result)
        
    def user_exists(self):
        return self.call('solverConfig') != 'User Error!'

