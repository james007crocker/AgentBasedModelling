import matplotlib.pyplot as plt
import numpy as np
from model import *
import sys

with open(sys.argv[1], 'r') as csvFile:
	lines = csvFile.readlines()
	if not lines:
		print('File Error')
		sys.exit(0)
	else:
		# if (lines[0].split(",")[0] != "Industries"):
		# 	print('File Error')
		# 	sys.exit(0)
		
		#Get all the industries
		industries = lines[1].split(",")
		for i in range(1, len(industries)):
			industries[i] = industries[i].rstrip()
		industries = industries[1:len(industries)]
		for industry in industries:
			print(industry)

		#Get the number of years of emissions data
		i = 2
		line = lines[i].split(",")
		while (line[0] != "Allowance Price"):
			i += 1
			line = lines[i].split(",")

		emissions = [[0 for industry in industries] for j in range(2, i)]
		for j in range(2, i):
			line = lines[j].split(",")
			for k in range(1, len(line)):
				emissions[j - 2][k - 1] = float(line[k])

		print("Emissions")
		for r in range(0, len(emissions)):
				print(emissions[r])

		#Get prices
		i += 2
		line = lines[i].split(",")
		j = i
		while (line[0] != "Cap"):
		 	i += 1
		 	line = lines[i].split(",")

		prices = [0 for k in range(j, i)]
		for k in range(j, i):
			line = lines[k].split(",")
			prices[k - j] = float(line[1])

		print("Prices")
		print(prices)

		#Get caps
		i += 2
		j = i
		line = lines[i].split(",")
		while(line[0] != "Cap Distribution"):
			i += 1
			line = lines[i].split(",")

		caps = [0 for k in range(j, i)]
		for k in range(j, i):
			line = lines[k].split(",")
			caps[k - j] = float(line[1])

		print("Caps")
		print(caps)

		#cap distribution
		i += 2
		capDistribution = [0 for industry in industries]
		line = lines[i].split(",")
		for k in range(0, len(industries)):
			capDistribution[k] = float(line[k])

		print("Cap Distribution")
		print(capDistribution)

		#price for investment
		i += 3
		priceInvestment = [0 for industry in industries]
		line = lines[i].split(",")
		for k in range(0, len(industries)):
			priceInvestment[k] = float(line[k])

		print("Price Investment")
		print(priceInvestment)

		#investment reduction factor
		i += 3
		investReducFactor = [0 for industry in industries]
		for k in range(0, len(industries)):
			investReducFactor[k] = float(line[k])

		print("Invest Reduction Factor")
		print(investReducFactor)
		#Get slope adjustment factor for allowances (per tonne)
		# i += 1
		# saf = lines[i].split(",")
		# for i in range(0, len(saf)):
		# 	saf[i] = float(saf[i])

		# print("Prices")
		# for r in range(0, len(prices)):
		# 		print(prices[r])


	allowances = [[0 for industry in industries] for i in range(0, len(caps))]
	for i in range(0, len(caps)):
		for j in range(0, len(industries)):
			allowances[i][j] = caps[i] * capDistribution[j]
		# print(allowances[i])

	model = CapTradeModel(industries, emissions, prices, priceInvestment, investReducFactor, allowances)
	for i in range(len(prices)):
		model.step()

	#Visualize results
	plt.figure(1)
	nrow = len(model.schedule.agents) / 2 + 1
	ncol = 2
	for i in range(0, len(model.schedule.agents)):
		if(model.schedule.agents[i].industryName == "Agriculture"):
			ax = plt.subplot(nrow, ncol, 1)
		elif(model.schedule.agents[i].industryName == "Waste"):
			ax = plt.subplot(nrow, ncol, 2)
		elif(model.schedule.agents[i].industryName == "Energy Producer"):
			ax = plt.subplot(nrow, ncol, 3)
		elif(model.schedule.agents[i].industryName == "Manufacturing"):
			ax = plt.subplot(nrow, ncol, 4)
		elif(model.schedule.agents[i].industryName == "Transportation"):
			ax = plt.subplot(nrow, ncol, 5)
		# ax = plt.subplot(nrow, ncol, i )
		ax.set_title(model.schedule.agents[i].industryName)
		x = np.asarray(list(range(2017 - len(emissions), 2017 + len(model.schedule.agents[i].carbonHistory) - len(emissions))))
		y = np.asarray(model.schedule.agents[i].carbonHistory)
		ax.plot(x, y, 'b')
		x = np.asarray(list(range(2017, 2017 + len(allowances))))
		y = np.asarray(model.schedule.agents[i].allowance)
		ax.plot(x, y, 'r')

	#plt.plot()
	

	plt.figure(1)
	ax = plt.subplot(nrow, ncol, 6)
	ax.set_title("Overall Results")
	Et = [0 for i in range(0, len(prices) + len(emissions))]
	for agent in model.schedule.agents:
		for i in range (0, len(agent.carbonHistory)):
			Et[i] += agent.carbonHistory[i]
	x = np.asarray(list(range(2017 - len(emissions), 2017 + len(Et) - len(emissions))))
	y = np.asarray(Et)
	ax.plot(x, y, "b")
	x = np.asarray(list(range(2017, 2017 + len(caps))))
	y = np.asarray(caps)
	ax.plot(x, y, "r")


	ax = plt.gca()
	ax.set_xticklabels([])
	plt.show()

	# for agent in model.schedule.agents:
	# 	print(agent.industryName)
	# 	print("Tech Investement, Credit Sold, Credit Bought")
	# 	for i in range(0, len(prices)):
	# 		print(agent.techInvestmentTime[i],",", agent.totalCreditPurchasedTime[i], ",", agent.totalCreditSoldTime[i])

	# nrow = len(model.schedule.agents) / 2 + 1
	# ncol = 2
	# for i in range(0, len(industries)):
	# 	ax = plt.subplot(nrow, ncol, i + 1)
	# 	ax.set_title(industries[i])
	# 	ax.hist([row[i] for row in unmetDemand], bins = 25)
	# plt.show()
	# print("Emissions: ", [row[0] for row in emissions])
	# print("carbonHistory: ", model.schedule.agents[0].carbonHistory)
	# print("Allowances: ", [row[0] for row in allowances])


	# unmetDemand = [[0 for industry in industry] for i in range(1000)]
	# totalEmissions = [[0 for industry in industries] for i in range(1000)]

	# for i in range(1000):
	# 	model = CapTradeModel(industries, emissions, prices, priceInvestment, investReducFactor, allowances)
	# 	#NOTE: npvHorizon < len(allowances) - steps
	# 	steps = len(allowances)
	# 	for k in range(steps):
	# 		model.step()
	# 	for agent in model.schedule.agents:
	# 		for j in range(0, len(industries)):
	# 			if (agent.industryName == industries[j]):
	# 				unmetDemand[i][j] = agent.totalFines
	# 				totalEmissions[i][j] = agent.carbonHistory[-1]

	# for i in range(0, len(industries)):
	# 	print(industries[i], ", ", np.median(unmetDemand[i]), ", ", np.median(totalEmissions[i]))


	# for i in range(0, len(industries)):
	# 	ax = plt.hist([row[i] for row in unmetDemand], bins = 25)
	# 	ax.set_title(industries[i])
	# 	plt.show()

	



	# totalEmissions = 0
	# for agent in model.schedule.agents:
	# 	totalEmissions += agent.carbonHistory[-1]
	# print("TOTAL EMISSIONS LAST PERIOD ", totalEmissions)


	



