mid/awbno
[to make the every data unique]
First col = awbno/mid to make every data unique 

Branch code REMARK = CD/SD
if branch = Trackon West/POST/DTDC(or other 3pl whch is not branch code)
then branch code = CD
else
branch code = SD

Address & pincode
pincode = pincode of the address fetch the area Name
Address = make geocode with pincode get the geocode of the address

Area name
Create this col based on address 
to get the area name map the address with the pincode area Name
based on the area name assign the cluster(area name)

roll qty
based on roll qty calculate the weight
weight = roll qty * 45/1000

remark based on vehical
if weight > 3.000 then remark = vehicle
else remark = normal

assign the delivry people
ignore the vehicle delivery
consider noramal delivery
assign the delivery to the agent
assign the delivery to the day



based on these conditions assign the delivery to the agent

if branch code =CD &
remark = normal &
weight = max_normal_weight (15-20) &
PINCODE = 1 TIME 1 PINCODE DELIVERY  or NEAREST PINCODE COVER) &
area name=  same or near to the pincode &
delivery count per day = 60-75
then assign the delivery to the agent

based on these conditions assign the delivery to the agent

to assign the day waise 
if agent1 is assigned to the delivery then assign the delivery to the agent1 on day1 of one area and that nearest delivery Address
then assign the delivery to the agent2 on day2 of one area and that nearest delivery Address

if the delivery assign to one agent then assign caonnot be repeated again
show the count of each day wise, agnet wise and also show the count of each day delivery
like this assign to the agent to the day waise


-> pincode wise area name 