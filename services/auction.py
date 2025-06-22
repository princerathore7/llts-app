from models.auction import Auction
from models import db
from datetime import datetime

def get_all_auctions():
    return [a.to_dict() for a in Auction.query.all()]

def get_auction_by_id(auction_id):
    auction = Auction.query.get(auction_id)
    return auction.to_dict() if auction else None

def create_auction(data, owner_id):
    new_auction = Auction(
        title=data.get('title'),
        description=data.get('description'),
        base_price=data.get('base_price'),
        end_date=datetime.strptime(data.get('end_date'), '%Y-%m-%d'),
        created_by=owner_id
    )
    db.session.add(new_auction)
    db.session.commit()
    return new_auction.to_dict()
