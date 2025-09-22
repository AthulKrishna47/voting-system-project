import mysql.connector as sqlcnt

# Establish database connection (ensure to replace with environment variables/config in practice)
try:
    connection = sqlcnt.connect(host='localhost', user='root', passwd='YOUR_PASSWORD', database='YOUR_DATABASE')
    if connection.is_connected():
        print("Connected to the database")
except sqlcnt.errors.InterfaceError as e:
    print(f"Error connecting to database: {e}")
    exit(1)

cursor = connection.cursor()

# Fetch all necessary data from database
def fetch_table_data():
    try:
        cursor.execute("SELECT * FROM voters")
        voters = cursor.fetchall()
        cursor.execute("SELECT * FROM candidate")
        candidates = cursor.fetchall()
        cursor.execute("SELECT * FROM votes")
        votes = cursor.fetchall()
        return voters, candidates, votes
    except sqlcnt.errors.DatabaseError as e:
        print(f"Error fetching data: {e}")
        exit(1)

voters_data, candidates_data, votes_data = fetch_table_data()

def login():
    print("Welcome to the Election Voting System!")
    global current_admission_no
    while True:
        try:
            admission_no = int(input("Enter admission number: "))
        except ValueError:
            print("Invalid input. Please enter a valid admission number (integer).")
            continue

        if any(admission_no in voter for voter in voters_data):
            print("Successfully logged in")
            current_admission_no = admission_no
            break
        else:
            print("Invalid admission number. Please try again.")
    print("=" * 100)

def update_vote(position, candidate_name):
    try:
        update_query = f"UPDATE votes SET {position} = %s WHERE admission_no = %s"
        cursor.execute(update_query, (candidate_name, current_admission_no))
        connection.commit()
        print(f"Vote for {candidate_name} as {position} successfully updated.")
    except sqlcnt.errors.DatabaseError as e:
        print(f"Database error while updating {position} vote: {e}")
        connection.rollback()

def get_candidates_by_position(position, house=None):
    if house:
        cursor.execute("SELECT * FROM candidate WHERE position = %s AND LOWER(house) = %s", (position, house.lower()))
    else:
        cursor.execute("SELECT * FROM candidate WHERE position = %s", (position,))
    return cursor.fetchall()

def select_candidate(position, candidates):
    if not candidates:
        print(f"No candidates found for {position}.")
        return None
    print(f"Candidates contesting for {position}:")
    candidate_dict = {}
    for idx, candidate in enumerate(candidates, 1):
        print(f"{idx}. {candidate[0]}")  # Assuming candidate name is at index 0
        candidate_dict[idx] = candidate[0]

    while True:
        try:
            choice = int(input(f"Enter the number associated with the candidate for {position}: "))
            if choice in candidate_dict:
                return candidate_dict[choice]
            else:
                print("Invalid choice number. Please select from the list.")
        except ValueError:
            print("Invalid input. Please enter a valid number.")

def vote_spl():
    spl_candidates = get_candidates_by_position("SPL")
    candidate_name = select_candidate("SPL", spl_candidates)
    if candidate_name:
        update_vote("spl", candidate_name)
    print("=" * 100)

def vote_captain():
    user_house = None
    for voter in voters_data:
        if current_admission_no in voter:
            user_house = voter[2]  # Assuming house is at index 2
            break

    if not user_house:
        print("Could not find your house information.")
        return

    captain_candidates = get_candidates_by_position("cap", user_house)
    candidate_name = select_candidate(f"{user_house} house Captain", captain_candidates)
    if candidate_name:
        update_vote("captain", candidate_name)
    print("=" * 100)

def display_spl_results():
    try:
        cursor.execute("SELECT spl, COUNT(*) FROM votes WHERE spl != '' GROUP BY spl")
        results = cursor.fetchall()
        if not results:
            print("No SPL votes recorded yet.")
            return

        max_votes = max(results, key=lambda x: x[1])[1]
        winners = [r[0] for r in results if r[1] == max_votes]

        print("\nSPL Election Results:")
        for winner in winners:
            print(f"Winner: {winner} with {max_votes} votes. Congratulations!")
    except sqlcnt.errors.DatabaseError as e:
        print(f"Error fetching SPL results: {e}")
    print("=" * 80)

def display_captain_results():
    try:
        cursor.execute("SELECT house, captain, COUNT(*) FROM votes WHERE captain != '' GROUP BY house, captain")
        results = cursor.fetchall()
        houses = {}

        for house, captain, count in results:
            if house not in houses:
                houses[house] = {}
            houses[house][captain] = count

        print("\nCaptain Elections Results:")
        for house, candidates in houses.items():
            max_votes = max(candidates.values())
            winners = [cand for cand, cnt in candidates.items() if cnt == max_votes]
            for winner in winners:
                print(f"{house.capitalize()} house winner: {winner} with {max_votes} votes. Congratulations!")
    except sqlcnt.errors.DatabaseError as e:
        print(f"Error fetching captain results: {e}")
    print("=" * 80)

def user_already_voted():
    for vote in votes_data:
        if current_admission_no in vote:
            spl_vote = vote[1]  # Assuming spl vote is at index 1
            captain_vote = vote[2]  # Assuming captain vote is at index 2
            return spl_vote != "" or captain_vote != ""
    return False

def main():
    while True:
        try:
            # Refresh data from DB in case of updates
            global voters_data, candidates_data, votes_data
            voters_data, candidates_data, votes_data = fetch_table_data()

            login()
            if user_already_voted():
                print("You have already voted and cannot vote again. Sorry!")
                print("=" * 100)
                break

            ready_to_vote = input("Are you ready to vote? (y/n): ").strip().lower()
            if ready_to_vote != 'y':
                print("You chose not to vote this time.")
                break

            vote_spl()
            vote_captain()

            see_results = input("Do you want to see the results? (y/n): ").strip().lower()
            if see_results == 'y':
                display_spl_results()
                display_captain_results()

            continue_voting = input("Do you want to continue voting? (y/n): ").strip().lower()
            if continue_voting != 'y':
                print("Thank you for voting! Exiting...")
                break

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            break

if __name__ == "__main__":
    main()
