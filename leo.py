import pygame

class Object:
  p=pygame.Vector2(0, 0)
  def __init__(x, y):
    p=pygame.Vector2(x, y)

class BackgroundObject(Object):
  
