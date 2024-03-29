import pygame 
from settings import *
from tile import Tile
from player import Player
from debug import debug
from support import *
from random import choice, randint
from weapon import Weapon
from ui import UI
from enemy import Enemy
from particles import AnimationPlayer

class Level:
	def __init__(self):

		#создали слой объектов
		self.display_surface = pygame.display.get_surface()

		#создали группу видимых элементов
		self.visible_sprites = YSortCameraGroup()
		self.obstacle_sprites = pygame.sprite.Group()#это понятно ~отрисовка точек

		# атака
		self.current_attack = None
		self.attack_sprites = pygame.sprite.Group()
		self.attackable_sprites = pygame.sprite.Group()

		self.create_map()

		self.ui = UI()


		self.animation_player = AnimationPlayer()

	def create_map(self):
		layouts = {
			'boundary': import_csv_layout('map/map_FloorBlocks.csv'),
			'grass': import_csv_layout('map/map_Grass.csv'),
			'object': import_csv_layout('map/map_Objects.csv'),
			'entities': import_csv_layout('map/map_Entities.csv')
		}
		graphics = {
			'grass': import_folder('graphics/Grass'),
			'objects': import_folder('graphics/objects')
		}

		for style,layout in layouts.items():
			for row_index,row in enumerate(layout):
				for col_index, col in enumerate(row):
					if col != '-1':
						x = col_index * TILESIZE
						y = row_index * TILESIZE
						if style == 'boundary':
							Tile((x,y),[self.obstacle_sprites],'invisible')
						if style == 'grass':
							random_grass_image = choice(graphics['grass'])
							Tile(
								(x,y),
								[self.visible_sprites,self.obstacle_sprites,self.attackable_sprites],
								'grass',
								random_grass_image)

						if style == 'object': # отрисовка объектов
							surf = graphics['objects'][int(col) - 10]
							Tile((x,y),[self.visible_sprites,self.obstacle_sprites],'object',surf)

						if style == 'entities':
							if col == '394':
								self.player = Player(
									(x,y),
									[self.visible_sprites],
									self.obstacle_sprites,
									self.create_attack,
									self.destroy_attack)
							else:
								monster_name = 'bamboo'
								Enemy(
									monster_name,
									(x,y),
									[self.visible_sprites,self.attackable_sprites],
									self.obstacle_sprites,
									self.damage_player,
									self.trigger_death_particles)

	def create_attack(self):
		
		self.current_attack = Weapon(self.player,[self.visible_sprites,self.attack_sprites])


	def destroy_attack(self):
		if self.current_attack:
			self.current_attack.kill()
		self.current_attack = None

	def player_attack_logic(self):
		if self.attack_sprites:
			for attack_sprite in self.attack_sprites:
				collision_sprites = pygame.sprite.spritecollide(attack_sprite,self.attackable_sprites,False)
				if collision_sprites:
					for target_sprite in collision_sprites:
						if target_sprite.sprite_type == 'grass':
							pos = target_sprite.rect.center
							offset = pygame.math.Vector2(0,75)
							for leaf in range(randint(3,6)):
								self.animation_player.create_grass_particles(pos - offset,[self.visible_sprites])
							target_sprite.kill()
						else:
							target_sprite.get_damage(self.player,attack_sprite.sprite_type)

	def damage_player(self,amount,attack_type):
		if self.player.vulnerable:
			self.player.health -= amount
			self.player.vulnerable = False
			self.player.hurt_time = pygame.time.get_ticks()
			self.animation_player.create_particles(attack_type,self.player.rect.center,[self.visible_sprites])

	def trigger_death_particles(self,pos,particle_type):

		self.animation_player.create_particles(particle_type,pos,self.visible_sprites)

	def run(self):
		self.visible_sprites.custom_draw(self.player)
		self.visible_sprites.update()
		self.visible_sprites.enemy_update(self.player)
		self.player_attack_logic()
		self.ui.display(self.player)


class YSortCameraGroup(pygame.sprite.Group):#класс для прикрепления камеры к игроку
	def __init__(self):

		#середина экрана по X-y и Y-y
		super().__init__()
		self.display_surface = pygame.display.get_surface()
		self.half_width = self.display_surface.get_size()[0] // 2
		self.half_height = self.display_surface.get_size()[1] // 2
		self.offset = pygame.math.Vector2()

		self.floor_surf = pygame.image.load('graphics/tilemap/map.png').convert()
		self.floor_rect = self.floor_surf.get_rect(topleft = (0,0))

	def custom_draw(self,player):

		self.offset.x = player.rect.centerx - self.half_width #координата x player-a
		self.offset.y = player.rect.centery - self.half_height #координата y player-a

		floor_offset_pos = self.floor_rect.topleft - self.offset
		self.display_surface.blit(self.floor_surf,floor_offset_pos)

		for sprite in sorted(self.sprites(),key = lambda sprite: sprite.rect.centery):
			offset_pos = sprite.rect.topleft - self.offset
			self.display_surface.blit(sprite.image,offset_pos)

	def enemy_update(self,player):
		enemy_sprites = [sprite for sprite in self.sprites() if hasattr(sprite,'sprite_type') and sprite.sprite_type == 'enemy']
		for enemy in enemy_sprites:
			enemy.enemy_update(player)
