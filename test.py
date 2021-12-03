import time

def main():
  start = time.time()
  print("Before sleep: ", time.time())
  time.sleep(20)
  print('Wake up after sleep: ', time.time())
  print('Ran for: ', time.time()-start)




if __name__ == '__main__':
  main()