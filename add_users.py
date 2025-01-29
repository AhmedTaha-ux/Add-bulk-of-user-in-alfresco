import requests
import pandas as pd
import base64
from deep_translator import GoogleTranslator
from settings import *

class AddUsers:

    def __init__(self, file_path):
        self.file_path = file_path
        self.groups_url = f"{ALFRESCO_URL}/groups"
        self.add_user_url = f"{ALFRESCO_URL}/people"
        self.encoded_credentials = base64.b64encode(f"{ALFRESCO_USERNAME}:{ALFRESCO_PASSWORD}".encode()).decode("utf-8")

        self.headers = {
            "Accept": "application/json",
            "Authorization": f"Basic {self.encoded_credentials}",
            "Content-Type": "application/json"
        }

    def get_groups(self):
        """
        Get all groups from alfresco

        :return: pd.DataFrame
        """
        groups_response = requests.get(self.groups_url, headers=self.headers)

        if groups_response.status_code != 200:
            raise Exception(f"Error fetching groups: {groups_response.status_code} {groups_response.text}")

        try:
            entries = groups_response.json()['list']['entries']
            groups = [entry['entry'] for entry in entries]
            groups_df = pd.DataFrame(groups)
        except (KeyError, TypeError, ValueError) as e:
            raise Exception(f"Error processing response JSON: {e}")

        return groups_df

    @staticmethod
    def translate_ar_to_en(string):
        """
        translate string to English
        :param string: string to be translated
        :return: string translated
        """
        return GoogleTranslator(source='ar', target='en').translate(string)


    def add_user(self):
        """
        Add user to alfresco and add to group
        :return: csv file with added user
        """
        # Open text files for logging success and failure messages
        with open("success_log.txt", "w", encoding="utf-8") as success_file, open("failed_log.txt", "w", encoding="utf-8") as failed_file:
            users = pd.read_csv(self.file_path)
            user_ids = []

            # Iterate through each row of the dataframe and process users
            for _, row in users.iterrows():
                try:
                    # Translate the first and last names
                    translated_name = self.translate_ar_to_en(row['name'])

                    group_df = self.get_groups()
                    mask = group_df['id'] == row['group']
                    group_name = group_df[mask]['displayName'].tolist()[0]
                    translated_group_name = self.translate_ar_to_en(group_name)

                    # Construct user id based on the translated names
                    user_id = f"{translated_group_name[0:3]}.{translated_name.replace(' ', '_')}"
                    user_ids.append(user_id)

                    # Create the user data to send in the POST request
                    user = {
                        "id": user_id,
                        "firstName": row['name'].split()[0],
                        "lastName": row['name'].split()[1],
                        "email": f'{user_id}@SCC.com',
                        "password": user_id
                    }

                    # groups_df = get_groups(get_groups_url, headers)
                    # # Verify if the group exists in groups_df
                    # mask = groups_df['displayName'] == row['group'].strip()
                    # group_matches = groups_df[ mask]['id'].tolist()
                    #
                    # if not group_matches:
                    #     failed_file.write(f"Group '{row['group']}' not found for user {user_id}. Skipping group assignment.\n")
                    #     continue  # Skip to the next user if the group is not found
                    #
                    # group_id = group_matches[0]  # Extract group ID if found

                    # Prepare group data for POST request
                    user_group = {
                        "username": user_id,
                        "groups": [
                            {
                                "expiryDate": "3000-12-01",
                                "userRole": row['group'],
                                "userId": user_id
                            },
                            {
                                "expiryDate": "3000-12-01",
                                "userRole": "GROUP_VIEW_STAT",
                                "userId": user_id
                            }
                        ],
                        "quota": -1
                    }

                    # Make the POST requests to add the user and assign the group
                    user_response = requests.post(self.add_user_url, headers=self.headers, json=user)
                    group_response = requests.post(UPDATE_URL, headers=self.headers, json=user_group)

                    # Check if user creation response was successful
                    if user_response.status_code == 201:
                        success_file.write(f"User {user_id} added successfully.\n")
                    else:
                        failed_file.write(f"Failed to create user {user_id}: {user_response.text}\n")

                    # Check if group assignment was successful
                    if group_response.status_code == 200:
                        success_file.write(f"User {user_id} assigned to group '{group_name}' successfully.\n")
                    else:
                        failed_file.write(f"Failed to assign user {user_id} to group '{group_name}': {group_response.text}\n")

                except Exception as e:
                    failed_file.write(f"Error while processing user {row['name'].split()[0]} {row['name'].split()[1]}: {e}\n")

        # Add user_id column to DataFrame and save to CSV
        users['user_name'] = user_ids
        users.to_csv('users_with_user_ids.csv', index=False)
