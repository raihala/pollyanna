import argparse
import csv
import datetime
import os
import sys


class Person(object):
    FIELD_DESCRIPTIONS = {
        'name': 'YOUR GIFTEE IS',
        'email': 'THEIR EMAIL IS',
        'address': 'SEND YOUR GIFT TO',
        'favorite_color': 'WHAT ARE THEIR FAVORITE COLORS/PATTERNS?',
        'restrictions': 'ANY ALLERGIES / RESTRICTIONS?',
        'gus_or_gary': 'ARE THEY A GRUMPY GUS OR A GOOFY GARY?',
        'functional_or_frivolous': 'ARE THEY FUNCTIONAL OR FRIVOLOUS?',
        'keepsake_or_consumable': 'DO THEY PREFER KEEPSAKES OR CONSUMABLES?',
        'tshirt_size_etc': 'ANY T-SHIRT SIZES, ETC?',
        'interview_responses': 'HOW DID THEY RESPOND TO THE CHILL INTERVIEWER?',
        'msg_to_santa': 'THEIR MESSAGE TO YOU',
        'msg_to_lucia': None,
        'reveal_receiving': None,
        'reveal_giving': None
    }
    FIELDS = list(FIELD_DESCRIPTIONS.keys())

    def __init__(self, **kwargs):
        # these fields are easy to handle
        self.name = kwargs['Name']
        self.email = kwargs['Email']
        self.favorite_color = kwargs.get('Favorite color?', '')

        # these ones are a little harder, but all pretty similar
        for key, value in kwargs.items():
            if key.startswith('Address'):
                self.address = value
            elif key.startswith('Allergies'):
                self.restrictions = value
            elif key.startswith('Do you prefer functional'):
                self.functional_or_frivolous = value
            elif key.startswith('Do you like keepsakes'):
                self.keepsake_or_consumable = value
            elif key.startswith('What size t-shirt'):
                self.tshirt_size_etc = value
            elif key.startswith("You're doing a job interview"):
                self.interview_responses = value
            elif key.startswith('General message for your'):
                self.msg_to_santa = value
            elif key.startswith('General message for ME'):
                self.msg_to_lucia = value
            elif key.startswith('Opt-in name reveal - RECEIVING'):
                self.reveal_receiving = value.startswith('YES')
            elif key.startswith('Opt-in name reveal - GIVING'):
                self.reveal_giving = value.startswith('YES')
            elif key.startswith('Are you a GRUMPY GUS'):
                self.gus_or_gary = value

        # populated later!
        self.recipient = None

    def to_dict(self):
        data = {field: getattr(self, field) for field in self.FIELDS}
        data['recipient_name'] = self.recipient.name
        return data

    def knows_recipient_identity(self):
        return self.reveal_giving or self.recipient.reveal_receiving

    def __hash__(self):
        string_value = ' '.join([
            f'{field}: {getattr(self, field)}'
            for field in self.FIELDS
        ])
        return hash(string_value)


def read_data_from_google_form_csv(filename):
    with open(filename, newline='') as f:
        reader = csv.DictReader(f)
        return [Person(**dict(row)) for row in reader]


def set_gift_giving_order(unrandomized_people):
    people = sorted(unrandomized_people, key=lambda p: hash(p))
    for i in range(len(people) - 1):
        people[i].recipient = people[i + 1]
    people[-1].recipient = people[0]


def write_reference_data(rows, target_dir=None, filename=None):
    """
    Writes a CSV file with output that we can reference at our leisure
    """
    fieldnames = Person.FIELDS + ['recipient_name']

    target_dir = target_dir or os.getcwd()
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    filename = filename or f"output_{timestamp}.csv"
    filepath = os.path.join(target_dir, filename)

    with open(filepath, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_email_attachment(giver, reveal_address=False, target_dir=None, filename=None):
    target_dir = target_dir or os.getcwd()
    filename = filename or giver.email or giver.name
    filepath = os.path.join(target_dir, filename)

    with open(filepath, 'w') as f:
        if not giver.knows_recipient_identity():
            if reveal_address:
                f.write("Your anonymous recipient's address is now included below!\n\n")
            else:
                f.write(
                    'You do NOT know who your giftee is! Hee hee. Message Lucia for '
                    'their address when you are ready to send your gift!\n\n'
                )
        for key, value in giver.recipient.to_dict().items():
            if key in ['recipient_name', 'msg_to_lucia', 'reveal_receiving', 'reveal_giving']:
                # they don't need to know..
                continue
            if key in ['name', 'email'] and not giver.knows_recipient_identity():
                # they don't need to know.......
                continue
            if key == 'address' and not giver.knows_recipient_identity() and not reveal_address:
                # they don't need to know...yet
                continue
            f.write(f'{Person.FIELD_DESCRIPTIONS[key]}: {value}\n')


def write_messages_to_lucia(people, target_dir=None, filename=None):
    target_dir = target_dir or os.getcwd()
    filename = filename or 'messages_to_Lucia.txt'
    filepath = os.path.join(target_dir, filename)

    with open(filepath, 'w') as f:
        f.write('Oh yeah!!!\n\n')
        for person in people:
            f.write(f'{person.name}: {person.msg_to_lucia}\n')
        f.write('\n\ni love you Lucia!!!! -puppy\n')


def main(argv=sys.argv):
    if os.environ.get('PYTHONHASHSEED', '') != '0':
        raise RuntimeError('You gotta set PYTHONHASHSEED=0 in the environment!!')

    parser = argparse.ArgumentParser()
    parser.add_argument('-f', dest='input_file', required=True)
    parser.add_argument('--reveal-addresses', dest='reveal_addresses', action='store_true')
    args = parser.parse_args(argv[1:])

    people = read_data_from_google_form_csv(args.input_file)
    set_gift_giving_order(people)

    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    output_data = [p.to_dict() for p in people]
    write_reference_data(output_data, target_dir=output_dir)
    write_messages_to_lucia(people, target_dir=output_dir)
    for person in people:
        write_email_attachment(person, reveal_address=args.reveal_addresses, target_dir=output_dir)


if __name__ == "__main__":
    sys.exit(main(argv=sys.argv))
