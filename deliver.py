 # Get today's date
    today = datetime.date.today()

    # Ask the user to select the start date
    start_date = st.date_input("Select the start date", value=today)

    # Ask the user to select the number of days
    days = st.number_input("Enter the number of days", min_value=1, value=8)

    # Generate the date range
    date_range = [start_date + datetime.timedelta(days=i) for i in range(days)]

    # Generate the date columns
    date_columns = [date.strftime("%d-%m-%Y") for date in date_range]