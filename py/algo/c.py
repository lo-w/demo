
print(0x5f375a86)


# image = [
# [0,0,0],
# [0,0,0]
# ]

# sr = 1
# sc = 0
# color = 2

# lenR = len(image)
# lenC = len(image[0])
# preC = image[sr][sc]

# for i in range(max(0, sr-1), min(lenR, sr+2)):
#     if image[i][sc] == preC:
#         image[i][sc] = color

# for j in range(max(0, sc-1), min(lenC, sc+2)):
#     if image[sr][j] == preC:
#         image[sr][j] = color

# print(image)

# m = 2
# n = 3
# indices = [[0,1],[1,1]]
# dp =  [[0]*n for _ in range(m)]
# for row in ([i[0] for i in indices]):
#     for i in range(n):
#         dp[row][i] += 1
# for col in ([i[1] for i in indices]):
#     for j in range(m):
#         dp[j][col] += 1
# res = 0
# for i in dp:
#     for j in i:
#         if j % 2 != 0:
#             res += 1
# row = [0]*m
# col = [0]*n
# for i, j in indices:
#     row[i] = 1-row[i]
#     col[j] = 1-col[j]
# res = 0
# for i in range(m):
#     for j in range(n):
#         if (row[i]+col[j])%2 == 1:
#             res += 1
# print(res)

# n = 0b00000000000000000000000000001011
# res = 0
# for _ in range(1, 32):
#     if n % 2 == 1:
#         res += 1
#     n = n >> 1

# for i in bin(n)[2:]:
#     res = res + 1 if i == '1' else res
# print(res)

# ops = [[2,2],[3,3],[3,3],[3,3],[2,2],[3,3],[3,3],[3,3],[2,2],[3,3],[3,3],[3,3]]
# res = 1
# a = 1
# for i in list(zip(*ops)):
#     a *= min(i)
# print(a)
# print(res)

# matrix = [[1,2,3],[4,5,6],[7,8,9]]
# list(zip(*matrix))
# def myzip(*iterables):
#     sentinel = object()
#     iterators = [iter(it) for it in iterables]
#     while iterators:
#         result = []
#         for it in iterators:
#             elem = next(it, sentinel)
#             if elem is sentinel:
#                 return
#             result.append(elem)
#         yield tuple(result)

# for i in myzip(*matrix):
#     print(i)

# def getR(poured, query_row, query_glass):
#     row = [poured]
#     print(row)
#     dp =  [[0]*101 for _ in range(101)]
#     dp[0][0] = poured
#     for i in range(query_row+1):
#         for j in range(i+1):
#             if dp[i][j] > 1:
#                 # print(dp[i][j])
#                 remain = (dp[i][j] - 1) / 2
#                 dp[i][j] = 1
#                 dp[i+1][j] += remain
#                 dp[i+1][j+1] += remain
#     return dp[query_row][query_glass]

# print(getR(5, 1, 1))

# i = 0
# for _ in iter(int, 1):
#     if i == len(nums)-1:
#         break
#     elif nums[i] == nums[i+1]:
#         nums.pop(i)
#     else:
#         i = i + 1


# nums = [4,4,2,4,3]
# nums = [1,1,1,1,1]

# rs = []
# for i in range(0, len(nums)):
#     for j in range(i +1, len(nums)):
#         for k in range(j +1, len(nums)):
#             if nums[i] != nums[j] and nums[i] != nums[k] and nums[j] != nums[k]:
#                 rs.append((i,j,k))
# print(rs)

# digits = [9]
# for i in range(len(digits)-1, -1, -1):
#     if digits[i] == 9:
#         digits[i] = 0
#         if i == 0:
#             print(digits.insert(0, 1))
#     else:
#         digits[i] = digits[i] + 1
#         break
# print(digits)

# gain = [-5,1,5,0,-7]
# s = 0
# c = [0]
# for i in gain:
#     s = s + i
#     c.append(s)
# print(max(c))

# from datetime import datetime

# def getT(n):
#     a = 101
#     b = 10000000

#     start =  datetime.now()
#     print(start)
#     for _ in range(0, n):
#         for i in range(a, b):
#             i % 2 < 1

#         # for i in range(a, b):
#         #     i & 1

#     end =  datetime.now()
#     print(end)
#     print("-" * 10)
#     print(end - start)

# getT(10)

# a = []
# def divisorGame(n: int) -> bool:
#     for i in range(n-1, 0, -1):
#         print("-"*20)
#         print(n)
#         print(i)
#         if n and n % i == 0:
#             a.append(1)
#             print(a)
#             n = divisorGame(n - i)
#             break
# n = 4
# print(divisorGame(n))
# print(len(a) & 1 > 0)

# def divideArray(nums):
#     # for i in set(nums):
#     #     if nums.count(i) % 2 != 0:
#     #         return False 
#     # return True
#     # return all(nums.count(i) % 2 == 0 for i in set(nums))

#     from collection.Collection import Counter
#     # a = Counter(nums)
#     # for i in a:
#     #     print(a[i])
#     #     if a[i] & 1 != 1:
#     #         return True
#     # return False
#     return all(i & 1 < 1 for i in Counter(nums).values())
# nums = [18,19,5,5,18,19,5,6,12,19,13,4,16,11,4,16,10,8,12,8,2,1,8,17,4,18,3,5,16,2,16,12,17,16,7,16,2,17,19,9,1,20,17,17,4,6]
# print(divideArray(nums))

# name  = "bdad"
# typed = "bbbd"

# def isLongPressedName(name: str, typed: str):
#     i = 0
#     if len(name) > len(typed):
#         return False
#     for j in range(0, len(typed)):
#         if name[i] == typed[j]:
#             if i == len(name) -1:
#                 for m in range(j, len(typed)):
#                     if name[i] != typed[m]:
#                         return False
#                 return True
#             elif j == len(typed) -1:
#                 if typed[-1] == name[-1]:
#                     return True
#             else:
#                 i = i + 1
#                 continue
        
#         elif (i > 0 and name[i-1] == typed[j]):
#             continue
#         else:
#             return False

#     return False

# print(isLongPressedName(name, typed))
# s = "abcba"
# target = "abc"
# print(int(min(s.count(i)/target.count(i) for i in set(target))))

# for i in range(97, 123):
#     print(chr(i))

# s = "acccad"
# t = -1
# for i in set(s):
#     if s.count(i) > 1:
#         print(i)
#         print(s.find(i))
#         print(s.rfind(i))
#         if s.rfind(i) - s.find(i) - 1 > t:
#             t = s.rfind(i) - s.find(i) - 1
#         print(t)

# print(max(s.rfind(i) - s.find(i) - 1 for i in  set(s)))


# ransomNote = "aa"
# magazine = "aab"

# a = set(ransomNote)

# print(a)

# for i in list(ransomNote.strip()):
#     print(i)
#     if i in magazine:
#         print(i)
#         ransomNote = ransomNote.replace(i,"",1)
#         magazine.replace(i,"",1)
#         print(ransomNote)
#         print(magazine)

# print(ransomNote)
# # print(b)

# for i in range(0, 5):
#     print(i)

# a = [2,3,3]

# print(sum(a))

# count = 5

# tmp = []
# d = {}
# nums = [4,1,4,0,3,5]

# print(nums)

# while len(nums):
#     mi = min(nums)
#     ma = max(nums)
#     # tmp.insert((mi+ma)/2)

#     d[(mi+ma)/2] = d.get((mi+ma)/2, 0) + 1

#     nums.remove(mi)
#     nums.remove(ma)

# tmp.insert()

# print(len(d.ke))

# for k in tmp:
#     d[k] = d.get(k, 0) + 1

# print(max(d.values()))
# if count % 2 == 0:
#     count = count >> 1
# else:
#     count = (count >> 1) + 1

# print(count & 1)


# nums = [1,1,2]


# d = {}
# for k in nums:
#     d[k] = d.get(k, 0) + 1

# nums = list(d.keys())
# print(nums)
# len(d.values())
