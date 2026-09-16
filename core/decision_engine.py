class DecisionEngine:

    def __init__(self):
        pass

    def recommend(self, event):

        severity = event["severity"]

        actions = []

        if severity == "Low":

            actions = [

                "Monitor situation",

                "Log event"

            ]

        elif severity == "Moderate":

            actions = [

                "Notify County Disaster Office",

                "Notify Fire Department",

                "Increase Monitoring"

            ]

        elif severity == "High":

            actions = [

                "Dispatch Fire Brigade",

                "Notify NDMA",

                "Notify Police",

                "Prepare Evacuation Teams"

            ]

        elif severity == "Extreme":

            actions = [

                "Dispatch Fire Brigade Immediately",

                "Notify National Disaster Operations Centre",

                "Deploy Aerial Surveillance",

                "Issue Public Warning",

                "Prepare Medical Response",

                "Prepare Evacuation"

            ]

        return {

            "recommended_actions": actions

        }

    def recommend_earthquake(self, event):

        severity = event["severity"]

        if severity == "Low":
            actions = ["Log event", "Monitor for aftershocks"]

        elif severity == "Moderate":
            actions = [
                "Notify County Disaster Office",
                "Alert nearby emergency services",
                "Monitor for aftershocks",
            ]

        elif severity == "High":
            actions = [
                "Notify National Disaster Operations Centre",
                "Dispatch damage assessment teams",
                "Alert hospitals in the affected county",
                "Prepare emergency shelters",
            ]

        elif severity == "Extreme":
            actions = [
                "Activate National Disaster Response",
                "Deploy Search and Rescue Teams",
                "Alert all hospitals and emergency services",
                "Issue Public Warning",
                "Prepare mass evacuation and shelter",
                "Request international assistance if needed",
            ]

        else:
            actions = ["Monitor situation"]

        return {"recommended_actions": actions}