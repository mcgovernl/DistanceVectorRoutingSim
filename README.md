# DistanceVectorRoutingSim
COSC465 Distance Vector Routing simulator

From class notes:

Algorithm run at each router
Start with empty vector
Add neighbors to vector
Send vector to neighbors
Receive a vector from a neighbor
For each item in the vector
If the router is not in your vector, add the router to your vector with a cost one greater than the cost received from your neighbor
If the router is in the vector and your cost is higher than your neighbor's cost plus one, update the cost
If any changes were made to your vector, send it to neighbors
Go back to step 4; stop when no more vectors are received
