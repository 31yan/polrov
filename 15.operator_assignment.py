# operasi yang dapat dilakukan dengan penyingkatan
# operasi ditambah dengan assignment

a = 5 # adalah assignment
print('nilai a =',a)

a += 1 # artinya adalah a = a + 1
print('nilai a += 1 nilai a menjadi',a)

a -= 2 # artinya adalah a = a - 2
print('nilai a -= 2 nilai a menjadi',a)

a *= 5 # artinya adalah a = a * 5
print('nilai a *= 5 nilai a menjadi',a)

a /= 2 # artinya adalah a = a / 2
print('nilai a /= 2 nilai a menjadi',a)

# modulus dan floor division
b = 10
print('\nnilai b =',b)

b %= 3 # artinya adalah b = b % 3
print('nilai b %= 3 nilai b menjadi',b)

c = 10
print('\nnilai c =',c)

c //= 3 # artinya adalah c = c // 3
print('nilai c //= 3 nilai c menjadi',c)

# pangkat
d = 5
print('\nnilai d =',d)
d **= 3 # artinya adalah d = d ** 3
print('nilai d **= 3 nilai d menjadi',d)

# operasi bitwise
# OR
e = True
print('\nnilai e |=',e)
e |= False
print('nilai e |= False, nilai e menjadi',e)

e = False
print('\nnilai e |=',e)
e |= False
print('nilai e |= False, nilai e menjadi',e)

# AND
e = True
print('\nnilai e &=',e)
e &= False
print('nilai e  &= False, nilai e menjadi',e)

e = True
print('\nnilai e &=',e)
e &= True
print('nilai e &= True, nilai e menjadi',e)

# XOR
e = True
print('\nnilai e ^=',e)
e ^= False
print('nilai e  ^= False, nilai e menjadi',e)

e = True
print('\nnilai e ^=',e)
e ^= True
print('nilai e ^= True, nilai e menjadi',e)

# shifting
f = 0b0100
print('\nnilai d =', format(f,'04b'))
f >>= 2
print('nilai f >>= 2, nilai f menjadi', format(f,'04b'))

f <<= 1
print('nilai f <<= 1, nilai f menjadi', format(f,'04b'))

