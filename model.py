import random
from random import randint

from queue import *

from mesa import Agent, Model
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector

#Linear Regression
from scipy import stats

#Expected reduction in emissions (Megatonnes) for each $ of investment
EMISSION_REDUCTION_INVESTMENT_FACTOR = 1
DISCOUNT_RATE = 1.06
PENALTY_FACTOR = 1

class Industry(Agent):
	def __init__(self, unique_id, model, industryName, carbonHistory, allowance, slopeFactor, Pr):
		super().__init__(unique_id, model)
		self.industryName = industryName
		self.carbonHistory = carbonHistory
		self.techInvestment = 0
		self.techInvestmentTime = []
		self.allowance = allowance
		self.creditsForSale = 0
		self.creditsToBuy = 0
		self.totalCreditsPurchased = 0
		self.totalCreditPurchasedTime = []
		self.totalRevenueSpentBuying = 0
		self.totalFines = 0
		self.totalCreditsSold = 0
		self.totalCreditSoldTime = []
		self.totalRevenueMadeSelling = 0
		self.slope = 0
		self.intercept = 0
		self.slopeFactor = slopeFactor
		self.Pr = Pr

	def step(self):
		#print(self.unique_id)
		price = self.model.prices[self.model.period]
		if (self.creditsForSale > 0):
			#Selling credits
			# print("SELL & BUY _ ", self.industryName)
			while (self.creditsForSale > 0 and not(self.model.buyers.empty())):
				other_agent = self.model.buyers.get()
				if (self.creditsForSale > other_agent.creditsToBuy):
					#Credits still to sell
					# print(self.industryName, " Selling ", other_agent.creditsToBuy, " to ", other_agent.industryName)
					self.creditsForSale -= other_agent.creditsToBuy					
					other_agent.totalCreditPurchasedTime.append(other_agent.creditsToBuy)
					other_agent.totalRevenueSpentBuying += other_agent.creditsToBuy * price
					self.totalRevenueMadeSelling += other_agent.creditsToBuy * price
					self.totalCreditsSold += other_agent.creditsToBuy
					other_agent.creditsToBuy = 0
				else:
					#All credits sold
					# print(self.industryName, " Selling ", self.creditsForSale, " to ", other_agent.industryName)
					other_agent.creditsToBuy -= self.creditsForSale
					other_agent.totalCreditsPurchased += self.creditsForSale
					other_agent.totalRevenueSpentBuying += self.creditsForSale * price
					self.totalRevenueMadeSelling += self.creditsForSale * price
					self.totalCreditsSold += self.creditsForSale
					self.creditsForSale = 0

					if (other_agent.creditsToBuy > 0):
						self.model.buyers.put(other_agent)

		elif (self.creditsToBuy > 0):
			#Buying credits

			while(self.creditsToBuy > 0 and not(self.model.sellers.empty())):
				
				other_agent = self.model.sellers.get()
				if (self.creditsToBuy < other_agent.creditsForSale):
					#Bought all credits
					# print(self.industryName, " Buying ", self.creditsToBuy, " from ", other_agent.industryName)
					other_agent.creditsForSale -= self.creditsToBuy
					other_agent.totalCreditsSold += self.creditsToBuy
					other_agent.totalRevenueMadeSelling += self.creditsToBuy * price
					self.totalRevenueSpentBuying += self.creditsToBuy * price
					self.totalCreditsPurchased += self.creditsToBuy
					self.creditsToBuy = 0

					if (other_agent.creditsForSale > 0):
						self.model.sellers.put(other_agent)
				else:
					#Credits still to buy
					# print(self.industryName, " Buying ", other_agent.creditsForSale, " from ", other_agent.industryName)
					self.creditsToBuy -= other_agent.creditsForSale
					self.totalCreditsPurchased += other_agent.creditsForSale
					other_agent.totalCreditsSold += other_agent.creditsForSale
					other_agent.totalRevenueMadeSelling += other_agent.creditsForSale * price
					self.totalRevenueSpentBuying += other_agent.creditsForSale * price
					other_agent.creditsForSale = 0
				
			#Check for fines
			if (self.creditsToBuy > 0):
				self.totalFines += PENALTY_FACTOR * self.creditsToBuy
				self.creditsToBuy = 0


	def forecast(self, period, price):
		slope = 0
		intercept = 0
		Ef = 0

		#Find current year emission
		if (period == 0):
			#Perform linear forecast of past emissions
			slope, intercept, r_value, p_value, std_err = stats.linregress(list(range(0, len(self.carbonHistory))), self.carbonHistory)
			Ef = slope * len(self.carbonHistory) + intercept
			self.slope = slope
			self.intercept = intercept
		else:
			#Build forecast based on investment in tech (adjusted slope)
			Ef = self.slope + self.intercept #self.slope * (len(self.carbonHistory) + period) + self.intercept
		#Check if running a surplus or deficit of credits
		Rreq = Ef - self.allowance[period]
		# print(self.industryName, " Rreq ", Rreq)

		if (Rreq > 0):
			#DEFICIT
			costBuy = price * Ef
			costInvest = self.Pr * Rreq + price * (Ef - Rreq)
			# if(self.industryName == "Transportation"):
			# 	print("Transportation: CostBuy: ", costBuy, " costInvest: ", costInvest)
			# 	print("price: ", price, " Rreq: ", Rreq, " Pr ", self.Pr, " Ef ", Ef)
			if (costBuy < costInvest):
				# print(self.industryName, " BUY ", self.slope)
				self.creditsToBuy = Rreq
				self.totalCreditPurchasedTime.append(Rreq)
				self.techInvestmentTime.append(0)
				self.totalCreditSoldTime.append(0)

			elif(costInvest < costBuy):
				# print(self.industryName, " INVEST ", self.slope)
				self.techInvestment += self.Pr * Rreq
				self.techInvestmentTime.append(self.Pr * Rreq)
				self.totalCreditSoldTime.append(0)
				self.totalCreditPurchasedTime.append(0)
				# self.slope = self.slope - self.Pr * Rreq * self.slopeFactor
				if (self.slope > 100):
					self.slope *= (1 - 0.2) + randint(-1, 1) / 100
				elif (self.slope < -100):
					self.slope *= (1 + 0.2) + randint(-1, 1) / 100
				else:
					self.slope = -101

		elif (Rreq < 0):
			#SURPLUS
			self.totalCreditPurchasedTime.append(0)
			self.techInvestmentTime.append(0)
			self.creditsForSale = abs(Rreq)
			self.totalCreditSoldTime.append(abs(Rreq))
		self.intercept = Ef
		self.carbonHistory.append(Ef)

class CapTradeModel(Model):
	def __init__(self, industries, carbonHistory, prices, priceInvestment, investReducFactor, allowances):
		#File parsing to initiate agents
		self.numIndustries = len(industries)
		self.period = -1
		self.buyers = Queue(len(industries))
		self.sellers = Queue(len(industries))
		self.schedule = RandomActivation(self)
		self.emissionHistLength = len(carbonHistory)

		self.prices = prices


		for i in range(0, len(industries)):
			agent = Industry(i, self, industries[i], [row[i] for row in carbonHistory], [row[i] for row in allowances], investReducFactor[i], priceInvestment[i])
			self.schedule.add(agent)

	def step(self):
		self.period += 1
		# print("******FORECAST*********")
		self.forecast()
		# print("******STEP*********")
		self.schedule.step()

	def forecast(self):
		self.buyers = Queue(self.numIndustries)
		self.sellers = Queue(self.numIndustries)
		#Current year price

		#Price scaling factor - slope of emissions/ slope of allowances
		# priceChange = 1

		# #Calculate future prices
		# #Find slope of allowance curve and emission curve
		# slopeA = 1
		# slopeE = 1
		# allowances = []
		# if (self.period == 0):
		# 	allowances = [0, 0]
		# 	for agent in self.schedule.agents:
		# 		allowances[0] += agent.allowance[0]
		# 		allowances[1] += agent.allowance[1]

		# 	slopeA, intercept, r_value, p_value, std_err = stats.linregress([0, 1], allowances)

		# 	emissions = [0 for i in range(0, self.emissionHistLength)]
		# 	for agent in self.schedule.agents:
		# 		for i in range(0, len(emissions)):
		# 			emissions[i] += agent.carbonHistory[i]
		# 	slopeE, intercept, r_value, p_value, std_err = stats.linregress(list(range(0, len(emissions))), emissions)
		# else:
		# 	allowances = [0 for i in range(0, self.period + 1)]
		# 	for agent in self.schedule.agents:
		# 		for i in range(0, self.period + 1):
		# 			allowances[i] += agent.allowance[i]
		# 	slopeA, intercept, r_value, p_value, std_err = stats.linregress(list(range(0, self.period + 1)), allowances)

		# 	slopeE = 0
		# 	for agent in self.schedule.agents:
		# 		slopeE += agent.slope
		# 		# print(agent.industryName, " ", agent.slope)

		# # print("SlopeA ", slopeA, " SlopeE ", slopeE)
		# #Price change (handle oo scenario?)
		# if (slopeE / slopeA == 0):
		# 	priceChange = abs(slopeA) / allowances[self.period]
		# elif (slopeE / slopeA > 1):
		# 	priceChange = slopeE / slopeA
		# elif (slopeE / slopeA < 1):
		# 	priceChange = 1 - slopeE / slopeA
		# else:
		# 	priceChange = 1

		for agent in self.schedule.agents:
			agent.forecast(self.period, self.prices[self.period])
			if (agent.creditsForSale > 0):
				self.sellers.put(agent)
			elif (agent.creditsToBuy > 0): 
				self.buyers.put(agent)
