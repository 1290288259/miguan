from flask import Blueprint, jsonify, request
from service.dashboard_service import DashboardService

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@dashboard_bp.route('/trend', methods=['GET'])
def get_trend():
    days = request.args.get('days', 7, type=int)
    granularity = request.args.get('granularity', 'day')
    data = DashboardService.get_attack_trend(days, granularity)
    return jsonify({'code': 200, 'data': data})

@dashboard_bp.route('/types', methods=['GET'])
def get_types():
    data = DashboardService.get_attack_type_stats()
    return jsonify({'code': 200, 'data': data})

@dashboard_bp.route('/map', methods=['GET'])
def get_map():
    data = DashboardService.get_map_data()
    return jsonify({'code': 200, 'data': data})

@dashboard_bp.route('/summary', methods=['GET'])
def get_summary():
    data = DashboardService.get_summary_stats()
    return jsonify({'code': 200, 'data': data})
